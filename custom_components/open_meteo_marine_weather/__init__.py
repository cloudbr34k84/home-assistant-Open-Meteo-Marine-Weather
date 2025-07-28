import logging
import asyncio
import time
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.network import async_get_source_ip
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .const import (
    DOMAIN, 
    PLATFORMS,
    API_HEALTH_CHECK_INTERVAL,
    API_HEALTH_CHECK_TIMEOUT,
    API_HEALTH_CHECK_ENDPOINT,
    API_HEALTH_CONSECUTIVE_FAILURES_THRESHOLD,
    API_HEALTH_RECOVERY_THRESHOLD,
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_UNHEALTHY,
    HEALTH_STATUS_UNKNOWN
)

_LOGGER = logging.getLogger(__name__)


class APIHealthMonitor:
    """Monitor API health status and track performance metrics."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the API health monitor."""
        self.hass = hass
        self._status = HEALTH_STATUS_UNKNOWN
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_check_time = None
        self._last_success_time = None
        self._last_failure_time = None
        self._response_times = []
        self._error_count = 0
        self._total_checks = 0
        self._health_check_task = None
        self._listeners = []
        
    @property
    def status(self) -> str:
        """Return current API health status."""
        return self._status
        
    @property
    def is_healthy(self) -> bool:
        """Return True if API is healthy."""
        return self._status == HEALTH_STATUS_HEALTHY
        
    @property
    def metrics(self) -> dict:
        """Return health metrics."""
        avg_response_time = None
        if self._response_times:
            avg_response_time = sum(self._response_times) / len(self._response_times)
            
        return {
            "status": self._status,
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "last_success_time": self._last_success_time.isoformat() if self._last_success_time else None,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "average_response_time": avg_response_time,
            "error_count": self._error_count,
            "total_checks": self._total_checks,
            "success_rate": (self._total_checks - self._error_count) / max(self._total_checks, 1) * 100
        }
    
    async def start_monitoring(self):
        """Start the health monitoring task."""
        if self._health_check_task is None or self._health_check_task.done():
            _LOGGER.info("Starting API health monitoring")
            self._health_check_task = asyncio.create_task(self._periodic_health_check())
            
    async def stop_monitoring(self):
        """Stop the health monitoring task."""
        if self._health_check_task and not self._health_check_task.done():
            _LOGGER.info("Stopping API health monitoring")
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            finally:
                self._health_check_task = None
                
    async def _periodic_health_check(self):
        """Perform periodic health checks."""
        while True:
            try:
                await asyncio.sleep(API_HEALTH_CHECK_INTERVAL)
                await self.check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error(f"Error in periodic health check: {e}")
                
    async def check_health(self) -> bool:
        """Perform a single health check."""
        start_time = time.time()
        self._last_check_time = datetime.now()
        self._total_checks += 1
        
        try:
            session = async_get_clientsession(self.hass)
            
            # Test endpoint with minimal parameters
            test_url = f"{API_HEALTH_CHECK_ENDPOINT}?latitude=0&longitude=0&current=wave_height"
            
            async with asyncio.timeout(API_HEALTH_CHECK_TIMEOUT):
                async with session.get(test_url) as response:
                    response_time = time.time() - start_time
                    
                    # Store response time (keep last 10 measurements)
                    self._response_times.append(response_time)
                    if len(self._response_times) > 10:
                        self._response_times.pop(0)
                    
                    if response.status == 200:
                        data = await response.json()
                        # Basic validation that the API returns expected structure
                        if "current" in data:
                            await self._handle_success(response_time)
                            return True
                        else:
                            await self._handle_failure("Invalid API response structure", response_time)
                            return False
                    else:
                        await self._handle_failure(f"HTTP {response.status}", response_time)
                        return False
                        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            await self._handle_failure("Timeout", response_time)
            return False
        except Exception as e:
            response_time = time.time() - start_time
            await self._handle_failure(str(e), response_time)
            return False
            
    async def _handle_success(self, response_time: float):
        """Handle successful health check."""
        self._consecutive_failures = 0
        self._consecutive_successes += 1
        self._last_success_time = datetime.now()
        
        # Update status based on response time and consecutive successes
        if response_time > 5.0:  # Slow response
            new_status = HEALTH_STATUS_DEGRADED
        elif self._consecutive_successes >= API_HEALTH_RECOVERY_THRESHOLD:
            new_status = HEALTH_STATUS_HEALTHY
        else:
            new_status = HEALTH_STATUS_DEGRADED
            
        await self._update_status(new_status)
        
        _LOGGER.debug(f"API health check successful: {response_time:.2f}s response time")
        
    async def _handle_failure(self, error: str, response_time: float):
        """Handle failed health check."""
        self._consecutive_successes = 0
        self._consecutive_failures += 1
        self._last_failure_time = datetime.now()
        self._error_count += 1
        
        # Update status based on consecutive failures
        if self._consecutive_failures >= API_HEALTH_CONSECUTIVE_FAILURES_THRESHOLD:
            new_status = HEALTH_STATUS_UNHEALTHY
        else:
            new_status = HEALTH_STATUS_DEGRADED
            
        await self._update_status(new_status)
        
        _LOGGER.warning(f"API health check failed: {error} (response time: {response_time:.2f}s)")
        
    async def _update_status(self, new_status: str):
        """Update health status and notify if changed."""
        if self._status != new_status:
            old_status = self._status
            self._status = new_status
            
            _LOGGER.info(f"API health status changed from {old_status} to {new_status}")
            
            # Fire event for status change
            self.hass.bus.async_fire(
                f"{DOMAIN}_api_health_status_changed",
                {
                    "old_status": old_status,
                    "new_status": new_status,
                    "metrics": self.metrics
                }
            )


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
        
        # Validate locations configuration
        locations = entry.data.get("locations")
        if locations is None or not isinstance(locations, list):
            _LOGGER.error("Invalid locations configuration - must be a list")
            raise ConfigEntryNotReady("Invalid locations configuration")
        
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
        
        # Create and initialize health monitor for this entry
        health_monitor = APIHealthMonitor(hass)
        hass.data[DOMAIN][entry.entry_id]["health_monitor"] = health_monitor
        await health_monitor.start_monitoring()
        
        # Perform initial health check before loading platforms
        initial_health = await health_monitor.check_health()
        
        if not initial_health:
            _LOGGER.warning("Initial API health check failed, but continuing with setup")
        else:
            _LOGGER.info("Initial API health check passed")
        
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
        
        # 4. Stop and cleanup health monitor for this entry
        health_monitor = entry_data.get("health_monitor")
        if health_monitor:
            _LOGGER.debug("Stopping health monitor for this entry")
            try:
                await health_monitor.stop_monitoring()
            except Exception as e:
                _LOGGER.warning(f"Error stopping health monitor during unload: {e}")
        
        # 5. Unload platforms with timeout
        try:
            async with asyncio.timeout(15):  # 15 second timeout for platform unload
                unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        except asyncio.TimeoutError:
            _LOGGER.error("Platform unload timed out for entry %s", entry.entry_id)
            return False
        
        # 6. Clean up entry data if unload was successful
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
