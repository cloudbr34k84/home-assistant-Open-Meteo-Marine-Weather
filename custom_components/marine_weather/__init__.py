import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery

DOMAIN = "marine_weather"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Marine Weather integration."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        _LOGGER.debug("Configuring Marine Weather integration from YAML configuration.")
        await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marine Weather from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Configuring Marine Weather integration from config entry.")
    
    # Load related platforms (e.g., sensors)
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry."""
    if DOMAIN in hass.data:
        hass.data.pop(DOMAIN)
    _LOGGER.debug("Unloading Marine Weather integration.")
    return True
