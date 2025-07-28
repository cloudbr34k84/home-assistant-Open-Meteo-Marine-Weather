"""Config flow for Marine Weather integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default locations for Marine Weather
DEFAULT_LOCATIONS = [
    {"name": "Alexandra Headlands", "latitude": -26.6715, "longitude": 153.1006},
    {"name": "Kings Beach", "latitude": -26.8017, "longitude": 153.1426},
    {"name": "Moffat Beach", "latitude": -26.7905, "longitude": 153.1400},
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Open Meteo Marine Weather"): cv.string,
        vol.Optional("locations", default=""): cv.string,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marine Weather."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidLocations:
                errors["locations"] = "invalid_locations"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidLocations(HomeAssistantError):
    """Error to indicate there is invalid location data."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Validate and parse locations
    locations = parse_locations(data.get("locations", ""))
    
    # If no locations provided or parsing failed, use defaults
    if not locations:
        locations = DEFAULT_LOCATIONS
        _LOGGER.info("Using default locations for Marine Weather integration")

    # Validate each location has required fields
    for location in locations:
        if not all(key in location for key in ["name", "latitude", "longitude"]):
            raise InvalidLocations("Location missing required fields")
        
        # Validate latitude and longitude ranges
        try:
            lat = float(location["latitude"])
            lon = float(location["longitude"])
            if not (-90 <= lat <= 90):
                raise InvalidLocations(f"Invalid latitude: {lat}")
            if not (-180 <= lon <= 180):
                raise InvalidLocations(f"Invalid longitude: {lon}")
        except (ValueError, TypeError) as err:
            raise InvalidLocations(f"Invalid coordinates: {err}") from err

    # Test API connectivity with first location (optional but recommended)
    try:
        first_location = locations[0]
        await test_api_connection(hass, first_location)
    except Exception as err:
        _LOGGER.warning("Could not test API connection: %s", err)
        # Don't fail setup if API test fails, just log warning

    # Return the data to be stored in the config entry
    return {
        "title": data["name"],
        "name": data["name"],
        "locations": locations,
    }


def parse_locations(locations_string: str) -> list[dict[str, Any]]:
    """Parse locations string into list of location dictionaries.
    
    Expected format: "Name1,lat1,lon1;Name2,lat2,lon2;..."
    Example: "Location A,-26.6715,153.1006;Location B,-26.8017,153.1426"
    """
    if not locations_string or not locations_string.strip():
        return []

    locations = []
    try:
        # Split by semicolon for multiple locations
        location_parts = locations_string.strip().split(";")
        
        for part in location_parts:
            if not part.strip():
                continue
                
            # Split by comma for name, lat, lon
            values = [v.strip() for v in part.split(",")]
            if len(values) != 3:
                _LOGGER.warning("Invalid location format: %s (expected: name,lat,lon)", part)
                continue
                
            name, lat_str, lon_str = values
            if not name:
                _LOGGER.warning("Empty location name in: %s", part)
                continue
                
            try:
                latitude = float(lat_str)
                longitude = float(lon_str)
            except ValueError as err:
                _LOGGER.warning("Invalid coordinates in %s: %s", part, err)
                continue
                
            locations.append({
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
            })
            
    except Exception as err:
        _LOGGER.error("Error parsing locations string '%s': %s", locations_string, err)
        return []

    return locations


async def test_api_connection(hass: HomeAssistant, location: dict[str, Any]) -> bool:
    """Test if we can connect to the Marine Weather API."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    
    session = async_get_clientsession(hass)
    
    # Test API endpoint with the provided location
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "wave_height",
        "timezone": "auto",
    }
    
    try:
        async with session.get(url, params=params, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                # Basic validation that we got expected data structure
                if "current" in data:
                    return True
            raise CannotConnect(f"API returned status {response.status}")
    except Exception as err:
        raise CannotConnect(f"Cannot connect to Marine Weather API: {err}") from err
