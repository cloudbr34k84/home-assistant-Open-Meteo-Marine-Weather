import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Minimal schema since this integration is configured only via platforms (YAML)
CONFIG_SCHEMA = cv.platform_only_config_schema(DOMAIN)


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
