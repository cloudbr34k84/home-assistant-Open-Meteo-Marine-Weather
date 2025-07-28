import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery
from homeassistant.exceptions import ConfigEntryNotReady

DOMAIN = "marine_weather"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Marine Weather integration."""
    try:
        hass.data.setdefault(DOMAIN, {})
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
        
        # Load related platforms (e.g., sensors)
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
        
        return True
    except ConfigEntryNotReady:
        raise
    except Exception as err:
        _LOGGER.error("Error setting up Marine Weather config entry: %s", err)
        raise ConfigEntryNotReady(f"Failed to setup Marine Weather: {err}") from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry."""
    try:
        # Unload platforms first
        unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
        
        if unload_ok and DOMAIN in hass.data:
            hass.data.pop(DOMAIN)
        
        _LOGGER.debug("Unloading Marine Weather integration.")
        return unload_ok
    except Exception as err:
        _LOGGER.error("Error unloading Marine Weather integration: %s", err)
        return False
