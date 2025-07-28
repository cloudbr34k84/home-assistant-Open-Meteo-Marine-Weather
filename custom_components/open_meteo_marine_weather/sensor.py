import logging
import aiohttp  # Import for asynchronous HTTP requests
import asyncio  # Import for using asyncio features
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfLength, UnitOfTime, DEGREE, PERCENTAGE
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # Import for getting the Home Assistant HTTP session
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
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

# Define the hardcoded locations for which the sensors will fetch data
LOCATIONS = [
    {"latitude": -26.6715, "longitude": 153.1006, "name": "Alexandra Headlands Surf Location"},
    {"latitude": -26.8017, "longitude": 153.1426, "name": "Kings Beach Surf Location"},
    {"latitude": -26.7905, "longitude": 153.1400, "name": "Moffat Beach Surf Location"},
]


class MarineWeatherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching marine weather data from the API."""

    def __init__(self, hass, health_monitor, location):
        """Initialize the coordinator."""
        self.health_monitor = health_monitor
        self.location = location
        
        # Update every 30 minutes to respect API limits
        super().__init__(
            hass,
            _LOGGER,
            name=f"MarineWeather-{location['name']}",
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self):
        """Fetch data from the API."""
        # Check API health before making request
        if self.health_monitor and not self.health_monitor.is_healthy:
            health_status = self.health_monitor.status
            if health_status == HEALTH_STATUS_UNHEALTHY:
                _LOGGER.warning(f"Skipping update for {self.location['name']} - API is unhealthy")
                # Return last known data instead of raising an exception
                return self.data
            elif health_status == HEALTH_STATUS_DEGRADED:
                _LOGGER.debug(f"API status is degraded for {self.location['name']}, proceeding with caution")

        try:
            session = async_get_clientsession(self.hass)
            
            async with asyncio.timeout(10):
                url = (
                    f"{API_URL}?latitude={self.location['latitude']}&longitude={self.location['longitude']}"
                    f"&current=wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,"
                    f"wind_wave_period,wind_wave_peak_period,swell_wave_height,swell_wave_direction,"
                    f"swell_wave_period,swell_wave_peak_period&timezone=Australia%2FSydney&models=best_match"
                )
                
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "current" not in data:
                        raise UpdateFailed(f"No 'current' data found in API response for {self.location['name']}")
                    
                    # Process and return the data
                    current_data = data["current"]
                    processed_data = {
                        "location": self.location,
                        "current": current_data,
                        "timezone": data.get("timezone", "Unknown"),
                        "models": "best_match",
                        "fetch_time": self.hass.loop.time(),
                    }
                    
                    # Add health metrics if available
                    if self.health_monitor:
                        metrics = self.health_monitor.metrics
                        processed_data["health_metrics"] = {
                            "status": self.health_monitor.status,
                            "success_rate": metrics.get('success_rate', 0),
                            "avg_response_time": metrics.get('average_response_time', 0),
                            "total_requests": metrics.get('total_requests', 0),
                            "failed_requests": metrics.get('error_count', 0),
                        }
                    
                    return processed_data

        except aiohttp.ClientResponseError as http_err:
            _LOGGER.error(f"HTTP error occurred while fetching data for {self.location['name']}: {http_err}")
            if self.health_monitor:
                asyncio.create_task(self.health_monitor.check_health())
            raise UpdateFailed(f"HTTP error: {http_err}")
            
        except aiohttp.ClientError as req_err:
            _LOGGER.error(f"Request exception occurred while fetching data for {self.location['name']}: {req_err}")
            if self.health_monitor:
                asyncio.create_task(self.health_monitor.check_health())
            raise UpdateFailed(f"Request error: {req_err}")
            
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout occurred while fetching data for {self.location['name']}")
            if self.health_monitor:
                asyncio.create_task(self.health_monitor.check_health())
            raise UpdateFailed("API request timeout")
            
        except ValueError as json_err:
            _LOGGER.error(f"JSON decode error occurred while processing response for {self.location['name']}: {json_err}")
            if self.health_monitor:
                asyncio.create_task(self.health_monitor.check_health())
            raise UpdateFailed(f"JSON decode error: {json_err}")
            
        except Exception as e:
            _LOGGER.error(f"Unexpected error occurred while fetching data for {self.location['name']}: {e}")
            if self.health_monitor:
                asyncio.create_task(self.health_monitor.check_health())
            raise UpdateFailed(f"Unexpected error: {e}")


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

class MarineWeatherCurrentSensor(CoordinatorEntity, SensorEntity):
    """
    Represents a sensor that fetches and provides current marine weather data
    such as swell wave height, direction, wave height, and wave direction.
    """
    def __init__(self, coordinator, location_name):
        # Initialize the coordinator entity
        super().__init__(coordinator)
        
        # Initialize the sensor with its location and name
        self.location = coordinator.location
        self._name = location_name
        self._attr_unique_id = f"{DOMAIN}_{self.location['name'].replace(' ', '_').lower()}_current"

    @property
    def name(self):
        """Return the name of the sensor to be displayed in the frontend."""
        return self._name

    @property
    def native_value(self):
        """Return the native value of the sensor (e.g., swell wave height in meters)."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data["current"].get("swell_wave_height")

    @property
    def state(self):
        """Return the current state of the sensor (deprecated, use native_value)."""
        return self.native_value

    @property
    def extra_state_attributes(self):
        """Return any additional attributes related to the sensor."""
        if not self.coordinator.data:
            return {}
            
        current_data = self.coordinator.data["current"]
        location = self.coordinator.data["location"]
        
        # Extract wave data from the coordinator's data
        swell_wave_height = current_data.get("swell_wave_height")
        swell_wave_direction_degrees = current_data.get("swell_wave_direction")
        wave_height = current_data.get("wave_height")
        wave_direction_degrees = current_data.get("wave_direction")
        swell_wave_period = current_data.get("swell_wave_period")
        swell_wave_peak_period = current_data.get("swell_wave_peak_period")
        
        attributes = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
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
            "timezone": self.coordinator.data.get("timezone", "Unknown"),
            "models": self.coordinator.data.get("models", "best_match"),
        }
        
        # Add API health metrics if available
        health_metrics = self.coordinator.data.get("health_metrics")
        if health_metrics:
            attributes.update({
                "api_health_status": health_metrics["status"],
                "api_success_rate": health_metrics["success_rate"],
                "api_success_rate_unit": PERCENTAGE,
                "api_avg_response_time": health_metrics["avg_response_time"],
                "api_avg_response_time_unit": UnitOfTime.SECONDS,
                "api_total_requests": health_metrics["total_requests"],
                "api_failed_requests": health_metrics["failed_requests"],
            })
        
        return attributes

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
        """Generate a unique ID for this sensor based on its location and name."""
        return self._attr_unique_id

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
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self):
        """Return device information for grouping sensors."""
        location = self.location
        return {
            "identifiers": {(DOMAIN, f"marine_weather_{location['latitude']}_{location['longitude']}")},
            "name": f"Marine Weather {location['name']}",
            "manufacturer": "Open Meteo",
            "model": "Marine Weather Station",
            "sw_version": "1.1",
            "entry_type": "service"
        }


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


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Marine Weather sensors from a config entry."""
    sensors = []
    coordinators = []

    # Get health monitor from entry data
    health_monitor = None
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        entry_data = hass.data[DOMAIN][entry.entry_id]
        health_monitor = entry_data.get("health_monitor")

    # Create API health sensor if health monitor is available
    if health_monitor:
        health_sensor = APIHealthSensor(health_monitor)
        health_sensor._entry_id = entry.entry_id
        sensors.append(health_sensor)

    # Get locations from config entry data, with fallback to default locations
    locations = entry.data.get("locations")
    if not locations:
        # Default locations if none provided in config entry
        locations = [
            {"latitude": -26.6715, "longitude": 153.1006, "name": "Alexandra Headlands"},
            {"latitude": -26.8017, "longitude": 153.1426, "name": "Kings Beach"},
            {"latitude": -26.7905, "longitude": 153.1400, "name": "Moffat Beach"},
        ]

    # Create coordinators and sensors for each location
    for location in locations:
        # Create a coordinator for this location
        coordinator = MarineWeatherDataUpdateCoordinator(hass, health_monitor, location)
        coordinators.append(coordinator)
        
        # Perform initial data fetch
        await coordinator.async_config_entry_first_refresh()
        
        # Create the sensor using the coordinator
        sensor = MarineWeatherCurrentSensor(coordinator, f"{location['name']} Current")
        sensor._entry_id = entry.entry_id
        sensors.append(sensor)

    # Store coordinators in entry data for cleanup
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id]["coordinators"].extend(coordinators)

    # Add all created sensors to Home Assistant
    async_add_entities(sensors, True)
