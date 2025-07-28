import logging
import aiohttp  # Import for asynchronous HTTP requests
import asyncio  # Import for using asyncio features
import async_timeout  # Add this import
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfLength, UnitOfTime, DEGREE, PERCENTAGE, UnitOfFrequency
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import Throttle
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # Import for getting the Home Assistant HTTP session
from homeassistant.helpers.debounce import Debouncer  # Import for handling debouncing/throttling
from homeassistant.helpers.event import async_track_time_interval  # Import for setting up periodic updates
from .const import (
    DOMAIN, 
    API_URL,
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_UNHEALTHY,
    HEALTH_STATUS_UNKNOWN
)

# Set up a logger for the component, which helps in logging error and debug messages
_LOGGER = logging.getLogger(__name__)

# Minimum time between updates to avoid overwhelming the API
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

# Define the hardcoded locations for which the sensors will fetch data
LOCATIONS = [
    {"latitude": -26.6715, "longitude": 153.1006, "name": "Alexandra Headlands Surf Location"},
    {"latitude": -26.8017, "longitude": 153.1426, "name": "Kings Beach Surf Location"},
    {"latitude": -26.7905, "longitude": 153.1400, "name": "Moffat Beach Surf Location"},
]

def degrees_to_compass(degrees):
    """
    Converts degrees into a 32-point compass rose direction.
    Returns 'Unknown' if degrees are None.
    Example: 0° = "N", 45° = "NE", 180° = "S", etc.
    """
    if degrees is None:
        return "Unknown"
    compass_directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16  # Convert degrees to the nearest compass direction index
    return compass_directions[index]

class MarineWeatherCurrentSensor(SensorEntity):
    """
    Represents a sensor that fetches and provides current marine weather data
    such as swell wave height, direction, wave height, and wave direction.
    """
    def __init__(self, latitude, longitude, name):
        # Initialize the sensor with its location and name
        self.latitude = latitude
        self.longitude = longitude
        self._name = name
        self._state = None  # The main state of the sensor (e.g., swell wave height)
        self._attributes = {}  # Additional attributes related to marine data
        self._debouncer = None  # Debouncer to avoid excessive updates

    @property
    def name(self):
        """Return the name of the sensor to be displayed in the frontend."""
        return self._name

    @property
    def native_value(self):
        """Return the native value of the sensor (e.g., swell wave height in meters)."""
        return self._state

    @property
    def state(self):
        """Return the current state of the sensor (deprecated, use native_value)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return any additional attributes related to the sensor (e.g., wave height, wave direction)."""
        return self._attributes

    @property
    def device_class(self):
        """Specify that this sensor is a distance measurement sensor."""
        return SensorDeviceClass.DISTANCE

    @property
    def state_class(self):
        """Return the state class for this sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        """The native unit of measurement for the sensor's state (meters for swell wave height)."""
        return UnitOfLength.METERS

    @property
    def unit_of_measurement(self):
        """The unit of measurement for the sensor's state (meters for swell wave height)."""
        return UnitOfLength.METERS

    @property
    def suggested_display_precision(self):
        """Return the suggested number of decimal places for display."""
        return 2

    @property
    def unique_id(self):
        """Generate a unique ID for this sensor based on its latitude, longitude, and name."""
        return f"{self.latitude}_{self.longitude}_{self._name.replace(' ', '_')}_current"

    @property
    def icon(self):
        """Set the icon used in the frontend for this sensor (surfing icon in this case)."""
        return "mdi:surfing"

    @property
    def entity_description(self):
        """Return entity description."""
        return f"Marine weather sensor for {self._name}"

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def device_info(self):
        """Return device information for grouping sensors."""
        return {
            "identifiers": {(DOMAIN, f"marine_weather_{self.latitude}_{self.longitude}")},
            "name": f"Marine Weather {self._name}",
            "manufacturer": "Open Meteo",
            "model": "Marine Weather Station",
            "sw_version": "1.1",
            "entry_type": "service"
        }

    async def async_added_to_hass(self):
        """
        This method is called when the sensor entity is added to Home Assistant.
        It sets up the debouncer and schedules regular updates.
        """
        # Set up Debouncer to manage throttling of API requests
        self._debouncer = Debouncer(
            hass=self.hass,
            logger=_LOGGER,
            cooldown=60,  # Minimum 60 seconds between update attempts
            immediate=True,
            function=self.async_update_data
        )
        
        # Schedule regular sensor updates using Home Assistant's event loop
        self._update_listener = async_track_time_interval(
            self.hass, self.async_update, MIN_TIME_BETWEEN_UPDATES
        )
        
        # Track this sensor and its resources for cleanup
        entry_id = getattr(self, '_entry_id', None)
        if entry_id and DOMAIN in self.hass.data and entry_id in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][entry_id]["sensors"].append(self)
            self.hass.data[DOMAIN][entry_id]["listeners"].append(self._update_listener)

    async def async_will_remove_from_hass(self):
        """
        This method is called when the sensor is about to be removed from Home Assistant.
        It performs cleanup of resources to prevent memory leaks.
        """
        try:
            # Cancel the scheduled updates
            if hasattr(self, '_update_listener') and self._update_listener:
                self._update_listener()
                self._update_listener = None
                _LOGGER.debug(f"Removed update listener for sensor {self._name}")
            
            # Clean up debouncer
            if self._debouncer:
                # Cancel any pending debounced calls
                try:
                    await self._debouncer.async_shutdown()
                except Exception as e:
                    _LOGGER.debug(f"Error shutting down debouncer for {self._name}: {e}")
                finally:
                    self._debouncer = None
                    _LOGGER.debug(f"Cleaned up debouncer for sensor {self._name}")
            
            # Clear state and attributes
            self._state = None
            self._attributes = {}
            
            _LOGGER.debug(f"Successfully cleaned up sensor {self._name}")
            
        except Exception as e:
            _LOGGER.error(f"Error during cleanup of sensor {self._name}: {e}")

    async def async_update(self):
        """
        This method is called periodically to update the sensor's data.
        It ensures that the update is throttled using the debouncer.
        """
        if not self._debouncer:
            _LOGGER.debug(f"Debouncer not initialized for sensor {self._name}. Skipping update.")
            return  # Exit if the debouncer hasn't been initialized

        _LOGGER.debug(f"Throttling update call for sensor {self._name}")
        await self._debouncer.async_call()

    async def async_update_data(self):
        """
        Fetch new data from the API for the sensor.
        This method runs asynchronously to avoid blocking Home Assistant's event loop.
        """
        # Get health monitor if available
        health_monitor = None
        if hasattr(self, 'hass') and DOMAIN in self.hass.data:
            health_monitor = self.hass.data[DOMAIN].get("health_monitor")
        
        # Check API health before making request
        if health_monitor and not health_monitor.is_healthy:
            health_status = health_monitor.status
            if health_status == HEALTH_STATUS_UNHEALTHY:
                _LOGGER.warning(f"Skipping update for {self._name} - API is unhealthy")
                # Don't clear existing data for unhealthy status, keep last known good values
                return
            elif health_status == HEALTH_STATUS_DEGRADED:
                _LOGGER.debug(f"API status is degraded for {self._name}, proceeding with caution")
        
        try:
            # Obtain the aiohttp session from Home Assistant
            session = async_get_clientsession(self.hass)
            
            # Fetch the current marine weather data from the API
            async with async_timeout.timeout(10):  # Adding timeout for API requests
                async with session.get(
                    f"{API_URL}?latitude={self.latitude}&longitude={self.longitude}&current=wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,wind_wave_peak_period,swell_wave_height,swell_wave_direction,swell_wave_period,swell_wave_peak_period&timezone=Australia%2FSydney&models=best_match"
                ) as response:
                    response.raise_for_status()  # Raise an error for bad HTTP status codes
                    data = await response.json()
                    
                    # Check if the API returned current data
                    if "current" in data:
                        # Extract swell wave data from the response
                        swell_wave_height = data["current"].get("swell_wave_height", None)
                        swell_wave_direction_degrees = data["current"].get("swell_wave_direction", None)
                        wave_height = data["current"].get("wave_height", None)
                        wave_direction_degrees = data["current"].get("wave_direction", None)
                        swell_wave_period = data["current"].get("swell_wave_period", None)
                        swell_wave_peak_period = data["current"].get("swell_wave_peak_period", None)
                        
                        # Set the main state of the sensor to swell_wave_height
                        self._state = swell_wave_height
                        self._attributes = {
                            "latitude": self.latitude,
                            "longitude": self.longitude,
                            "swell_wave_height": swell_wave_height,
                            "swell_wave_height_unit": UnitOfLength.METERS,
                            "swell_wave_direction": swell_wave_direction_degrees,
                            "swell_wave_direction_unit": DEGREE,
                            "swell_wave_direction_name": degrees_to_compass(swell_wave_direction_degrees),
                            "swell_wave_period": swell_wave_period,
                            "swell_wave_period_unit": UnitOfTime.SECONDS,
                            "swell_wave_peak_period": swell_wave_peak_period,
                            "swell_wave_peak_period_unit": UnitOfTime.SECONDS,
                            "wave_height": wave_height,
                            "wave_height_unit": UnitOfLength.METERS,
                            "wave_direction": wave_direction_degrees,
                            "wave_direction_unit": DEGREE,
                            "wave_direction_name": degrees_to_compass(wave_direction_degrees),
                            "timezone": data.get("timezone", "Unknown"),
                            "models": "best_match",
                        }
                        
                        # Add API health status to attributes if available
                        if health_monitor:
                            self._attributes["api_health_status"] = health_monitor.status
                            metrics = health_monitor.metrics
                            self._attributes["api_success_rate"] = metrics.get('success_rate', 0)
                            self._attributes["api_success_rate_unit"] = PERCENTAGE
                            self._attributes["api_avg_response_time"] = metrics.get('average_response_time', 0)
                            self._attributes["api_avg_response_time_unit"] = UnitOfTime.SECONDS
                            self._attributes["api_total_requests"] = metrics.get('total_requests', 0)
                            self._attributes["api_failed_requests"] = metrics.get('failed_requests', 0)
                        
                    else:
                        _LOGGER.error(f"No 'current' data found in the API response for {self._name}. Response: {data}")

        except aiohttp.ClientResponseError as http_err:
            _LOGGER.error(f"HTTP error occurred while fetching current data for {self._name}: {http_err}")
            # On error, trigger health check if monitor is available
            if health_monitor:
                asyncio.create_task(health_monitor.check_health())
            # Don't clear existing data on HTTP errors, keep last known good values
        except aiohttp.ClientError as req_err:
            _LOGGER.error(f"Request exception occurred while fetching current data for {self._name}: {req_err}")
            # On error, trigger health check if monitor is available
            if health_monitor:
                asyncio.create_task(health_monitor.check_health())
            # Don't clear existing data on client errors, keep last known good values
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout occurred while fetching current data for {self._name}")
            # On timeout, trigger health check if monitor is available
            if health_monitor:
                asyncio.create_task(health_monitor.check_health())
            # Don't clear existing data on timeout, keep last known good values
        except ValueError as json_err:
            _LOGGER.error(f"JSON decode error occurred while processing the response for {self._name}: {json_err}")
            # On JSON error, trigger health check if monitor is available
            if health_monitor:
                asyncio.create_task(health_monitor.check_health())
            # Clear data on JSON errors as the response is corrupted
            self._state = None
            self._attributes = {}
        except Exception as e:
            _LOGGER.error(f"Unexpected error occurred while fetching current data for {self._name}: {e}")
            # On unexpected error, trigger health check if monitor is available
            if health_monitor:
                asyncio.create_task(health_monitor.check_health())
            # Clear data on unexpected errors
            self._state = None
            self._attributes = {}


class APIHealthSensor(SensorEntity):
    """
    Sensor that reports API health status and metrics.
    """
    
    def __init__(self, health_monitor):
        """Initialize the API health sensor."""
        self._health_monitor = health_monitor
        self._name = "Open Meteo Marine Weather API Health"
        self._state = None
        self._attributes = {}
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
        
    @property
    def native_value(self):
        """Return the current API health status."""
        return self._state
        
    @property
    def state(self):
        """Return the current API health status (deprecated, use native_value)."""
        return self._state
        
    @property
    def extra_state_attributes(self):
        """Return additional health metrics."""
        return self._attributes
        
    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.ENUM
        
    @property
    def state_class(self):
        """Return the state class (None for diagnostic sensors)."""
        return None
        
    @property
    def entity_category(self):
        """Return the entity category."""
        return EntityCategory.DIAGNOSTIC
        
    @property
    def options(self):
        """Return the list of possible states."""
        return [
            HEALTH_STATUS_HEALTHY,
            HEALTH_STATUS_DEGRADED,
            HEALTH_STATUS_UNHEALTHY,
            HEALTH_STATUS_UNKNOWN
        ]
        
    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_api_health"
        
    @property
    def icon(self):
        """Return the icon for this sensor."""
        if self._state == HEALTH_STATUS_HEALTHY:
            return "mdi:check-circle"
        elif self._state == HEALTH_STATUS_DEGRADED:
            return "mdi:alert-circle"
        elif self._state == HEALTH_STATUS_UNHEALTHY:
            return "mdi:close-circle"
        else:
            return "mdi:help-circle"

    @property
    def entity_description(self):
        """Return entity description."""
        return "API health status for Open Meteo Marine Weather service"

    @property
    def available(self):
        """Return True if entity is available."""
        return self._health_monitor is not None

    @property
    def device_info(self):
        """Return device information for grouping sensors."""
        return {
            "identifiers": {(DOMAIN, "api_health_monitor")},
            "name": "Open Meteo Marine Weather API",
            "manufacturer": "Open Meteo",
            "model": "API Health Monitor",
            "sw_version": "1.1",
            "entry_type": "service"
        }
            
    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        # Initial update
        await self.async_update()
        
        # Track this sensor for cleanup
        entry_id = getattr(self, '_entry_id', None)
        if entry_id and DOMAIN in self.hass.data and entry_id in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][entry_id]["sensors"].append(self)
            
    async def async_update(self):
        """Update the sensor with current health status."""
        if self._health_monitor:
            self._state = self._health_monitor.status
            metrics = self._health_monitor.metrics
            self._attributes = {
                "success_rate": metrics.get('success_rate', 0),
                "success_rate_unit": PERCENTAGE,
                "average_response_time": metrics.get('average_response_time', 0),
                "average_response_time_unit": UnitOfTime.SECONDS,
                "total_requests": metrics.get('total_requests', 0),
                "failed_requests": metrics.get('failed_requests', 0),
                "consecutive_failures": metrics.get('consecutive_failures', 0),
                "last_success": metrics.get('last_success'),
                "last_failure": metrics.get('last_failure'),
            }
        else:
            self._state = HEALTH_STATUS_UNKNOWN
            self._attributes = {}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """
    Set up the Marine Weather sensors asynchronously.
    Creates a sensor for each predefined location in LOCATIONS.
    """
    sensors = []

    # Loop through the hardcoded locations and create sensors for each
    for location in LOCATIONS:
        latitude = location["latitude"]
        longitude = location["longitude"]
        name = location["name"]

        # Create the current condition sensor and add it to the list of sensors
        sensor = MarineWeatherCurrentSensor(latitude, longitude, f"{name} Current")
        sensors.append(sensor)

    # Add all created sensors to Home Assistant in an async way
    async_add_entities(sensors, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Marine Weather sensors from a config entry."""
    sensors = []

    # Get health monitor from hass data
    health_monitor = None
    if DOMAIN in hass.data and "health_monitor" in hass.data[DOMAIN]:
        health_monitor = hass.data[DOMAIN]["health_monitor"]

    # Create API health sensor if health monitor is available
    if health_monitor:
        health_sensor = APIHealthSensor(health_monitor)
        health_sensor._entry_id = entry.entry_id
        sensors.append(health_sensor)

    # Loop through the hardcoded locations and create sensors for each
    for location in LOCATIONS:
        latitude = location["latitude"]
        longitude = location["longitude"]
        name = location["name"]

        # Create the current condition sensor
        sensor = MarineWeatherCurrentSensor(latitude, longitude, f"{name} Current")
        
        # Store entry_id in sensor for cleanup tracking
        sensor._entry_id = entry.entry_id
        sensors.append(sensor)

    # Add all created sensors to Home Assistant
    async_add_entities(sensors, True)
