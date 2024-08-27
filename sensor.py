import requests
import logging
from datetime import timedelta, datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import LENGTH_METERS, SPEED_KILOMETERS_PER_HOUR, TIME_SECONDS, DEGREE
from homeassistant.util import Throttle
from .const import DOMAIN, API_URL

# Set up a logger for the component
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
    Converts degrees to a 32-point compass rose direction.
    Handles None values by returning 'Unknown'.
    """
    if degrees is None:
        return "Unknown"
    compass_directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16
    return compass_directions[index]

class MarineWeatherCurrentSensor(SensorEntity):
    """
    Represents a sensor that provides current marine weather data, such as wave height and direction.
    """
    def __init__(self, latitude, longitude, name):
        self.latitude = latitude
        self.longitude = longitude
        self._name = name
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes of the sensor."""
        return self._attributes

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return "measurement"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return LENGTH_METERS  # Assuming wave height as the primary state

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{self.latitude}_{self.longitude}_{self._name.replace(' ', '_')}_current"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor, throttled to avoid excessive API calls."""
        try:
            # Make an API request to fetch the current marine weather data
            response = requests.get(
                f"{API_URL}?latitude={self.latitude}&longitude={self.longitude}&current=wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,wind_wave_peak_period,swell_wave_height,swell_wave_direction,swell_wave_period,swell_wave_peak_period&timezone=Australia%2FSydney&models=best_match"
            )
            response.raise_for_status()  # Raise an error for bad HTTP status codes
            data = response.json()
            
            if "current" in data:
                # Extract relevant data from the response
                wave_height = data["current"].get("wave_height", None)
                wave_direction_degrees = data["current"].get("wave_direction", None)
                swell_wave_height = data["current"].get("swell_wave_height", None)
                swell_wave_direction_degrees = data["current"].get("swell_wave_direction", None)
                swell_wave_period = data["current"].get("swell_wave_period", None)
                swell_wave_peak_period = data["current"].get("swell_wave_peak_period", None)

                # Set the wave height as the main state of the sensor
                self._state = wave_height  
                # Set additional attributes that describe the current marine conditions
                self._attributes = {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "wave_height": f"{wave_height} m" if wave_height is not None else "Unknown",
                    "wave_direction": wave_direction_degrees,
                    "wave_direction_name": degrees_to_compass(wave_direction_degrees),
                    "swell_wave_height": f"{swell_wave_height} m" if swell_wave_height is not None else "Unknown",
                    "swell_wave_direction": swell_wave_direction_degrees,
                    "swell_wave_direction_name": degrees_to_compass(swell_wave_direction_degrees),
                    "swell_wave_period": f"{swell_wave_period} s" if swell_wave_period is not None else "Unknown",
                    "swell_wave_peak_period": f"{swell_wave_peak_period} s" if swell_wave_peak_period is not None else "Unknown",
                    "timezone": data.get("timezone", "Unknown"),
                    "models": "best_match",
                }
            else:
                _LOGGER.error(f"No 'current' data found in the API response for {self._name}. Response: {data}")

        except requests.exceptions.HTTPError as http_err:
            _LOGGER.error(f"HTTP error occurred while fetching current data for {self._name}: {http_err}")
            self._state = None
            self._attributes = {}
        except requests.exceptions.RequestException as req_err:
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

class MarineWeatherForecastAttributeSensor(SensorEntity):
    """
    Represents a sensor that provides a specific marine weather forecast attribute for a specific day.
    """
    def __init__(self, latitude, longitude, name, day_index, attribute_name, unit, device_class):
        self.latitude = latitude
        self.longitude = longitude
        self._name = name
        self._day_index = day_index
        self._attribute_name = attribute_name
        self._unit_of_measurement = unit
        self._device_class = device_class
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Day {self._day_index + 1} {self._attribute_name.replace('_', ' ').title()}"

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes of the sensor."""
        attributes = self._attributes.copy()

        # Add direction name with explanation for directional attributes
        if "direction" in self._attribute_name:
            direction_degrees = self._state
            if direction_degrees is not None:
                direction_name = degrees_to_compass(direction_degrees)
                opposite_direction = degrees_to_compass((direction_degrees + 180) % 360)
                attributes["direction_name"] = f"{direction_name} (from {direction_name} towards {opposite_direction})"
        
        # Convert forecast date to DD/MM/YYYY HH:MM:SS format
        if "forecast_date" in attributes:
            attributes["forecast_date"] = [
                datetime.fromisoformat(date).strftime('%d/%m/%Y %H:%M:%S')
                for date in attributes["forecast_date"]
            ]
        
        return attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{self.latitude}_{self.longitude}_{self._name.replace(' ', '_')}_day_{self._day_index}_{self._attribute_name.replace(' ', '_')}"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor, throttled to avoid excessive API calls."""
        try:
            # Make an API request to fetch the hourly marine weather forecast data
            response = requests.get(
                f"{API_URL}?latitude={self.latitude}&longitude={self.longitude}&hourly={self._attribute_name}&timezone=Australia%2FSydney&forecast_days=5&models=best_match"
            )
            response.raise_for_status()  # Raise an error for bad HTTP status codes
            data = response.json()

            if "hourly" in data and self._attribute_name in data["hourly"]:
                # Extract the specific attribute data for the selected day
                start_hour = self._day_index * 24
                end_hour = start_hour + 24
                attribute_values = data["hourly"][self._attribute_name][start_hour:end_hour]
                forecast_dates = data["hourly"]["time"][start_hour:end_hour]

                # Set the first value of the day as the main state
                self._state = attribute_values[0] if attribute_values else None

                # Set additional attributes if needed
                self._attributes = {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    f"{self._attribute_name}_values": attribute_values,
                    "timezone": data.get("timezone", "Unknown"),
                    "forecast_date": forecast_dates,
                    "models": "best_match",
                }
            else:
                _LOGGER.error(f"No 'hourly' data found for {self._attribute_name} in the API response for {self._name}. Response: {data}")

        except requests.exceptions.HTTPError as http_err:
            _LOGGER.error(f"HTTP error occurred while fetching forecast data for {self._name}: {http_err}")
            self._state = None
            self._attributes = {}
        except requests.exceptions.RequestException as req_err:
            _LOGGER.error(f"Request exception occurred while fetching forecast data for {self._name}: {req_err}")
            self._state = None
            self._attributes = {}
        except ValueError as json_err:
            _LOGGER.error(f"JSON decode error occurred while processing the forecast response for {self._name}: {json_err}")
            self._state = None
            self._attributes = {}
        except Exception as e:
            _LOGGER.error(f"Unexpected error occurred while fetching forecast data for {self._name}: {e}")
            self._state = None
            self._attributes = {}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Marine Weather sensors."""
    sensors = []

    # List of attributes to create sensors for, along with their units and device classes
    attributes = [
        ("wave_height", LENGTH_METERS, "measurement"),
        ("wave_direction", DEGREE, "measurement"),
        ("wave_period", TIME_SECONDS, "measurement"),
        ("swell_wave_height", LENGTH_METERS, "measurement"),
        ("swell_wave_direction", DEGREE, "measurement"),
        ("swell_wave_period", TIME_SECONDS, "measurement"),
        ("wind_wave_height", LENGTH_METERS, "measurement"),
        ("wind_wave_direction", DEGREE, "measurement"),
        ("wind_wave_period", TIME_SECONDS, "measurement"),
        ("ocean_current_velocity", SPEED_KILOMETERS_PER_HOUR, "measurement"),
        ("ocean_current_direction", DEGREE, "measurement")
    ]

    # Loop through the hardcoded locations and create sensors for each
    for location in LOCATIONS:
        latitude = location["latitude"]
        longitude = location["longitude"]
        name = location["name"]

        # Create the current condition sensor, excluding ocean current velocity and direction
        sensors.append(MarineWeatherCurrentSensor(latitude, longitude, f"{name} Current"))

        # Create forecast sensors for each day and attribute
        for day in range(1, 6):  # Loop over 5 days, starting from day 1
            for attribute, unit, device_class in attributes:
                sensors.append(MarineWeatherForecastAttributeSensor(
                    latitude, longitude, name, day - 1, attribute, unit, device_class
                ))

    # Add all created sensors to the Home Assistant platform
    add_entities(sensors, True)
