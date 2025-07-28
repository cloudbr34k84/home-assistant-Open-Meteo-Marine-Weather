import logging
import asyncio
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.service import async_register_admin_service

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
    try:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug("Configuring Marine Weather integration from config entry.")
        
        # Validate config entry data
        if not entry.data:
            _LOGGER.error("Config entry data is missing")
            raise ConfigEntryNotReady("Config entry data is missing")
        
        # Store entry-specific data for cleanup tracking
        hass.data[DOMAIN][entry.entry_id] = {
            "sensors": [],
            "listeners": [],
            "tasks": [],
            "sessions": []
        }
        
        # Load related platforms (e.g., sensors)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        return True
    except ConfigEntryNotReady:
        raise
    except Exception as err:
        _LOGGER.error("Error setting up Marine Weather config entry: %s", err)
        raise ConfigEntryNotReady(f"Failed to setup Marine Weather: {err}") from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry with comprehensive resource cleanup."""
    try:
        _LOGGER.debug(f"Starting unload process for entry {entry.entry_id}")
        
        # Get entry-specific data for cleanup
        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        
        # 1. Cancel any running background tasks
        tasks = entry_data.get("tasks", [])
        if tasks:
            _LOGGER.debug(f"Cancelling {len(tasks)} background tasks")
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        _LOGGER.warning(f"Error cancelling task during unload: {e}")
        
        # 2. Remove event listeners
        listeners = entry_data.get("listeners", [])
        if listeners:
            _LOGGER.debug(f"Removing {len(listeners)} event listeners")
            for listener in listeners:
                try:
                    listener()  # Most HA listeners return an unsubscribe function
                except Exception as e:
                    _LOGGER.warning(f"Error removing listener during unload: {e}")
        
        # 3. Close any HTTP sessions (if we had custom ones)
        sessions = entry_data.get("sessions", [])
        if sessions:
            _LOGGER.debug(f"Closing {len(sessions)} HTTP sessions")
            for session in sessions:
                try:
                    if hasattr(session, 'close') and not session.closed:
                        await session.close()
                except Exception as e:
                    _LOGGER.warning(f"Error closing session during unload: {e}")
        
        # 4. Unload platforms first
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        # 5. Clean up entry data
        if unload_ok and DOMAIN in hass.data:
            # Remove this specific entry's data
            hass.data[DOMAIN].pop(entry.entry_id, None)
            
            # If no more entries, remove the domain data entirely
            if not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN, None)
        
        if unload_ok:
            _LOGGER.debug(f"Successfully unloaded Marine Weather integration entry {entry.entry_id}")
        else:
            _LOGGER.warning(f"Failed to unload some platforms for entry {entry.entry_id}")
            
        return unload_ok
        
    except Exception as err:
        _LOGGER.error(f"Error unloading Marine Weather integration entry {entry.entry_id}: {err}")
        return False

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
