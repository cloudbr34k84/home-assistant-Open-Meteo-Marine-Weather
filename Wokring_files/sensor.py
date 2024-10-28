import requests
import logging
import aiohttp  # Import for asynchronous HTTP requests
import asyncio  # Import for using asyncio features
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import LENGTH_METERS, DEGREE
from homeassistant.util import Throttle
from homeassistant.helpers.aiohttp_client import async_get_clientsession  # Import for getting the Home Assistant HTTP session
from homeassistant.helpers.debounce import Debouncer  # Import for handling debouncing/throttling
from homeassistant.helpers.event import async_track_time_interval  # Import for setting up periodic updates
from .const import DOMAIN, API_URL

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
    def state(self):
        """Return the current state of the sensor (e.g., swell wave height in meters)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return any additional attributes related to the sensor (e.g., wave height, wave direction)."""
        return self._attributes

    @property
    def device_class(self):
        """Specify that this sensor is a measurement sensor."""
        return "measurement"

    @property
    def unit_of_measurement(self):
        """The unit of measurement for the sensor's state (meters for swell wave height)."""
        return LENGTH_METERS

    @property
    def unique_id(self):
        """Generate a unique ID for this sensor based on its latitude, longitude, and name."""
        return f"{self.latitude}_{self.longitude}_{self._name.replace(' ', '_')}_current"

    @property
    def icon(self):
        """Set the icon used in the frontend for this sensor (surfing icon in this case)."""
        return "mdi:surfing"

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

    async def async_update(self, time=None):
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
        try:
            # Obtain the aiohttp session from Home Assistant
            session = async_get_clientsession(self.hass)
            
            # Fetch the current marine weather data from the API
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
                        "swell_wave_height": f"{swell_wave_height} m" if swell_wave_height is not None else "Unknown",
                        "swell_wave_direction": swell_wave_direction_degrees,
                        "swell_wave_direction_name": degrees_to_compass(swell_wave_direction_degrees),
                        "swell_wave_period": f"{swell_wave_period} s" if swell_wave_period is not None else "Unknown",
                        "swell_wave_peak_period": f"{swell_wave_peak_period} s" if swell_wave_peak_period is not None else "Unknown",
                        "wave_height": f"{wave_height} m" if wave_height is not None else "Unknown",
                        "wave_direction": wave_direction_degrees,
                        "wave_direction_name": degrees_to_compass(wave_direction_degrees),
                        "timezone": data.get("timezone", "Unknown"),
                        "models": "best_match",
                    }
                else:
                    _LOGGER.error(f"No 'current' data found in the API response for {self._name}. Response: {data}")

        except aiohttp.ClientResponseError as http_err:
            _LOGGER.error(f"HTTP error occurred while fetching current data for {self._name}: {http_err}")
            self._state = None
            self._attributes = {}
        except aiohttp.ClientError as req_err:
            _LOGGER.error(f"Request exception occurred while fetching current data for {self._name}: {req_err}")
            self._state = None
            self._attributes = {}
        except ValueError as json_err:
            _LOGGER.error(f"JSON decode error occurred while processing the response for {self._name}: {json_err}")
            self._state = None
            self._attributes = {}
        except Exception as e:
            _LOGGER.error(f"Unexpected error occurred while fetching current data for {self._name}: {e}")
            self._state = None
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
        sensors.append(MarineWeatherCurrentSensor(latitude, longitude, f"{name} Current"))

    # Add all created sensors to Home Assistant in an async way
    async_add_entities(sensors, True)
