import logging
import asyncio
import time
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.helpers import discovery
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.network import async_get_source_ip

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Marine Weather integration."""
    try:
        hass.data.setdefault(DOMAIN, {})
        
        # Register reload service
        async def async_reload_service_handler(service_call: ServiceCall) -> None:
            """Handle reload service call."""
            _LOGGER.info("Reloading Open Meteo Marine Weather integration")
            config_entries = hass.config_entries.async_entries(DOMAIN)
            reload_tasks = [
                hass.config_entries.async_reload(entry.entry_id)
                for entry in config_entries
            ]
            if reload_tasks:
                await asyncio.gather(*reload_tasks)
        
        # Register cleanup service for manual resource cleanup
        async def async_cleanup_service_handler(service_call: ServiceCall) -> None:
            """Handle manual cleanup service call."""
            _LOGGER.info("Manual cleanup requested for Open Meteo Marine Weather integration")
            try:
                # Force cleanup of any lingering resources
                for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
                    if isinstance(entry_data, dict):
                        # Cancel any running tasks
                        for task in entry_data.get("tasks", []):
                            if not task.done():
                                task.cancel()
                        
                        # Remove listeners
                        for listener in entry_data.get("listeners", []):
                            try:
                                listener()
                            except Exception:
                                pass
                                
                        # Close sessions
                        for session in entry_data.get("sessions", []):
                            try:
                                if hasattr(session, 'close') and not session.closed:
                                    await session.close()
                            except Exception:
                                pass
                
                _LOGGER.info("Manual cleanup completed")
            except Exception as e:
                _LOGGER.error(f"Error during manual cleanup: {e}")
        
        async_register_admin_service(
            hass,
            DOMAIN,
            "reload",
            async_reload_service_handler,
        )
        
        async_register_admin_service(
            hass,
            DOMAIN,
            "cleanup",
            async_cleanup_service_handler,
        )
        
        if DOMAIN in config:
            _LOGGER.debug("Configuring Marine Weather integration from YAML configuration.")
            await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
        return True
    except Exception as err:
        _LOGGER.error("Error setting up Marine Weather integration: %s", err)
        return False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marine Weather from a config entry."""
    start_time = time.time()
    start_memory = None
    
    # Get initial memory usage if psutil is available
    if PSUTIL_AVAILABLE:
        try:
            start_memory = psutil.Process().memory_info().rss
        except Exception:
            start_memory = None
    
    try:
        # Validate entry state
        if entry.state != ConfigEntryState.NOT_LOADED:
            _LOGGER.warning("Entry is already loaded or in invalid state: %s", entry.state)
            return False
        
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug("Configuring Marine Weather integration from config entry.")
        
        # Validate required configuration data
        if not entry.data:
            _LOGGER.error("Config entry data is missing")
            raise ConfigEntryNotReady("Config entry data is missing")
        
        # Validate required configuration fields
        if not entry.data.get("latitude") or not entry.data.get("longitude"):
            _LOGGER.error("Missing required configuration data (latitude/longitude)")
            raise ConfigEntryNotReady("Missing required configuration data")
        
        # Check network connectivity before setup
        try:
            async with asyncio.timeout(10):
                source_ip = await async_get_source_ip(hass, target_ip="8.8.8.8")
                if not source_ip:
                    _LOGGER.warning("No internet connectivity detected, setup may fail")
        except asyncio.TimeoutError:
            _LOGGER.warning("Network connectivity check timed out")
        except Exception:
            _LOGGER.warning("Could not verify internet connectivity")
        
        # Store entry-specific data for cleanup tracking
        hass.data[DOMAIN][entry.entry_id] = {
            "sensors": [],
            "listeners": [],
            "tasks": [],
            "sessions": [],
            "coordinators": []
        }
        
        # Load related platforms with timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with asyncio.timeout(30):  # 30 second timeout for platform setup
                    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
                break
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    _LOGGER.error("Platform setup timed out after %d attempts", max_retries)
                    raise ConfigEntryNotReady("Platform setup timed out")
                _LOGGER.warning("Platform setup attempt %d timed out, retrying", attempt + 1)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as err:
                if attempt == max_retries - 1:
                    raise
                _LOGGER.warning("Setup attempt %d failed, retrying: %s", attempt + 1, err)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        setup_time = time.time() - start_time
        
        # Log performance metrics
        if PSUTIL_AVAILABLE and start_memory is not None:
            try:
                memory_used = psutil.Process().memory_info().rss - start_memory
                _LOGGER.debug(
                    "Setup completed in %.2fs, memory usage: %d bytes",
                    setup_time,
                    memory_used
                )
            except Exception:
                _LOGGER.debug("Setup completed in %.2fs", setup_time)
        else:
            _LOGGER.debug("Setup completed in %.2fs", setup_time)
        
        if setup_time > 30:
            _LOGGER.warning("Setup took longer than expected: %.2fs", setup_time)
        
        return True
    except ConfigEntryNotReady:
        raise
    except asyncio.TimeoutError:
        setup_time = time.time() - start_time
        _LOGGER.error("Setup timed out after %.2fs", setup_time)
        raise ConfigEntryNotReady("Setup timed out")
    except Exception as err:
        setup_time = time.time() - start_time
        _LOGGER.error("Error setting up Marine Weather config entry after %.2fs: %s", setup_time, err)
        # Clean up any partial setup
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id, None)
        raise ConfigEntryNotReady(f"Failed to setup Marine Weather: {err}") from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry with comprehensive resource cleanup."""
    start_time = time.time()
    
    try:
        _LOGGER.debug(f"Starting unload process for entry {entry.entry_id}")
        
        # Validate entry is actually loaded
        if entry.entry_id not in hass.data.get(DOMAIN, {}):
            _LOGGER.warning("Entry %s not found in data store", entry.entry_id)
            return True  # Consider it successfully unloaded
        
        # Get entry-specific data for cleanup
        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        
        # 1. Cancel any running background tasks with timeout
        tasks = entry_data.get("tasks", [])
        if tasks:
            _LOGGER.debug(f"Cancelling {len(tasks)} background tasks")
            try:
                async with asyncio.timeout(10):  # 10 second timeout for task cleanup
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                            except Exception as e:
                                _LOGGER.warning(f"Error cancelling task during unload: {e}")
            except asyncio.TimeoutError:
                _LOGGER.warning("Task cancellation timed out during unload")
        
        # 2. Remove event listeners
        listeners = entry_data.get("listeners", [])
        if listeners:
            _LOGGER.debug(f"Removing {len(listeners)} event listeners")
            for listener in listeners:
                try:
                    listener()  # Most HA listeners return an unsubscribe function
                except Exception as e:
                    _LOGGER.warning(f"Error removing listener during unload: {e}")
        
        # 3. Close any HTTP sessions and coordinators
        sessions = entry_data.get("sessions", [])
        coordinators = entry_data.get("coordinators", [])
        
        if sessions or coordinators:
            _LOGGER.debug(f"Closing {len(sessions)} HTTP sessions and {len(coordinators)} coordinators")
            try:
                async with asyncio.timeout(5):  # 5 second timeout for session cleanup
                    # Close coordinators first
                    for coordinator in coordinators:
                        try:
                            if hasattr(coordinator, 'async_shutdown'):
                                await coordinator.async_shutdown()
                            elif hasattr(coordinator, '_session') and coordinator._session:
                                if not coordinator._session.closed:
                                    await coordinator._session.close()
                        except Exception as e:
                            _LOGGER.warning(f"Error shutting down coordinator during unload: {e}")
                    
                    # Then close other sessions
                    for session in sessions:
                        try:
                            if hasattr(session, 'close') and not session.closed:
                                await session.close()
                        except Exception as e:
                            _LOGGER.warning(f"Error closing session during unload: {e}")
            except asyncio.TimeoutError:
                _LOGGER.warning("Session/coordinator cleanup timed out during unload")
        
        # 4. Unload platforms with timeout
        try:
            async with asyncio.timeout(15):  # 15 second timeout for platform unload
                unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        except asyncio.TimeoutError:
            _LOGGER.error("Platform unload timed out for entry %s", entry.entry_id)
            return False
        
        # 5. Clean up entry data if unload was successful
        if unload_ok and DOMAIN in hass.data:
            # Remove this specific entry's data
            hass.data[DOMAIN].pop(entry.entry_id, None)
            
            # If no more entries, remove the domain data entirely
            if not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN, None)
        
        unload_time = time.time() - start_time
        if unload_ok:
            _LOGGER.debug(f"Successfully unloaded Marine Weather integration entry {entry.entry_id} in %.2fs", unload_time)
        else:
            _LOGGER.warning(f"Failed to unload some platforms for entry {entry.entry_id} after %.2fs", unload_time)
        
        if unload_time > 20:
            _LOGGER.warning("Unload took longer than expected: %.2fs", unload_time)
            
        return unload_ok
        
    except asyncio.TimeoutError:
        unload_time = time.time() - start_time
        _LOGGER.error("Unload timed out for entry %s after %.2fs", entry.entry_id, unload_time)
        return False
    except Exception as err:
        unload_time = time.time() - start_time
        _LOGGER.error(f"Error unloading Marine Weather integration entry {entry.entry_id} after %.2fs: {err}", unload_time)
        return False

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
