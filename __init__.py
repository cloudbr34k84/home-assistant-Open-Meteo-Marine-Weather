from homeassistant.core import HomeAssistant

DOMAIN = "marine_weather"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Marine Weather integration."""
    return True
