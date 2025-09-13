import logging
import aiohttp  # Import for asynchronous HTTP requests
import asyncio  # Import for using asyncio features
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.util.unit_system import UnitOfLength
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.debounce import Debouncer
from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

# Minimum time between updates to avoid overwhelming the API
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)


def degrees_to_compass(degrees):
    """Convert degrees into compass direction."""
    if degrees is None:
        return "Unknown"
    compass_directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16
    return compass_directions[index]


class MarineWeatherCurrentSensor(SensorEntity):
    """Sensor for current marine weather conditions."""

    def __init__(self, latitude, longitude, name, timezone="UTC"):
        self.latitude = latitude
        self.longitude = longitude
        self._name = name
        self._timezone = timezone
        self._state = None
        self._attributes = {}
        self._debouncer = None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def device_class(self):
        return "measurement"

    @property
    def unit_of_measurement(self):
        return UnitOfLength.METERS

    @property
    def unique_id(self):
        return f"{self.latitude}_{self.longitude}_{self._name.replace(' ', '_')}_current"

    @property
    def icon(self):
        return "mdi:surfing"

    async def async_added_to_hass(self):
        """Called when entity is added to Home Assistant."""
        self._debouncer = Debouncer(
            hass=self.hass,
            logger=_LOGGER,
            cooldown=60,
            immediate=True,
            function=self.async_update_data,
        )
        _LOGGER.debug(f"MarineWeatherCurrentSensor for {self._name} added.")
        self._update_listener = async_track_time_interval(
            self.hass, self.async_update, MIN_TIME_BETWEEN_UPDATES
        )

    async def async_update(self, time=None):
        if not self._debouncer:
            _LOGGER.debug(f"Debouncer not initialized for {self._name}. Skipping update.")
            return
        await self._debouncer.async_call()

    async def async_update_data(self):
        """Fetch data from the Marine Weather API."""
        try:
            session = async_get_clientsession(self.hass)
            url = (
                f"{API_URL}?latitude={self.latitude}&longitude={self.longitude}"
                f"&current=wave_height,wave_direction,wave_period,"
                f"wind_wave_height,wind_wave_direction,wind_wave_period,wind_wave_peak_period,"
                f"swell_wave_height,swell_wave_direction,swell_wave_period,swell_wave_peak_period"
                f"&timezone={self._timezone}&models=best_match"
            )

            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                if "current" in data:
                    swell_wave_height = data["current"].get("swell_wave_height")
                    swell_wave_direction_degrees = data["current"].get("swell_wave_direction")
                    wave_height = data["current"].get("wave_height")
                    wave_direction_degrees = data["current"].get("wave_direction")
                    swell_wave_period = data["current"].get("swell_wave_period")
                    swell_wave_peak_period = data["current"].get("swell_wave_peak_period")

                    self._state = swell_wave_height
                    self._attributes = {
                        "latitude": self.latitude,
                        "longitude": self.longitude,
                        "swell_wave_height": f"{swell_wave_height} m" if swell_wave_height else "Unknown",
                        "swell_wave_direction": swell_wave_direction_degrees,
                        "swell_wave_direction_name": degrees_to_compass(swell_wave_direction_degrees),
                        "swell_wave_period": f"{swell_wave_period} s" if swell_wave_period else "Unknown",
                        "swell_wave_peak_period": f"{swell_wave_peak_period} s" if swell_wave_peak_period else "Unknown",
                        "wave_height": f"{wave_height} m" if wave_height else "Unknown",
                        "wave_direction": wave_direction_degrees,
                        "wave_direction_name": degrees_to_compass(wave_direction_degrees),
                        "timezone": data.get("timezone", self._timezone),
                        "models": "best_match",
                    }
                else:
                    _LOGGER.error(f"No 'current' data found for {self._name}. Response: {data}")

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Request error for {self._name}: {e}")
            self._state = None
            self._attributes = {}
        except ValueError as e:
            _LOGGER.error(f"JSON decode error for {self._name}: {e}")
            self._state = None
            self._attributes = {}
        except Exception as e:
            _LOGGER.error(f"Unexpected error for {self._name}: {e}")
            self._state = None
            self._attributes = {}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Marine Weather platform via YAML."""
    sensors = []
    locations = config.get("locations", [])
    for location in locations:
        latitude = location["latitude"]
        longitude = location["longitude"]
        name = location["name"]
        timezone = location.get("timezone", "UTC")
        sensors.append(MarineWeatherCurrentSensor(latitude, longitude, f"{name} Current", timezone))
    async_add_entities(sensors, True)
