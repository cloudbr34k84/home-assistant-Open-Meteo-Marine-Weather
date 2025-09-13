"""Diagnostics support for Marine Weather integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "state": entry.state.value,
            "unique_id": entry.unique_id,
        },
        "config": {
            # Redact sensitive data
            "latitude": entry.data.get("latitude"),
            "longitude": entry.data.get("longitude"),
        },
        "api_health": None,
        "sensors": [],
        "statistics": {
            "total_sensors": 0,
            "active_sensors": 0,
        }
    }
    
    # Get health monitor data if available
    if DOMAIN in hass.data and "health_monitor" in hass.data[DOMAIN]:
        health_monitor = hass.data[DOMAIN]["health_monitor"]
        diagnostics_data["api_health"] = health_monitor.metrics
    
    # Get entry-specific data
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    
    # Count sensors
    sensors = entry_data.get("sensors", [])
    diagnostics_data["statistics"]["total_sensors"] = len(sensors)
    
    # Collect sensor information
    for sensor in sensors:
        if hasattr(sensor, "name") and hasattr(sensor, "state"):
            sensor_info = {
                "name": sensor.name,
                "state": sensor.state,
                "unique_id": getattr(sensor, "unique_id", None),
                "device_class": getattr(sensor, "device_class", None),
                "unit_of_measurement": getattr(sensor, "unit_of_measurement", None),
                "available": getattr(sensor, "available", True),
            }
            
            # Check if sensor has valid state (is active)
            if sensor.state is not None:
                diagnostics_data["statistics"]["active_sensors"] += 1
                
            diagnostics_data["sensors"].append(sensor_info)
    
    # Add resource usage information
    diagnostics_data["resources"] = {
        "tasks": len(entry_data.get("tasks", [])),
        "listeners": len(entry_data.get("listeners", [])),
        "sessions": len(entry_data.get("sessions", [])),
        "coordinators": len(entry_data.get("coordinators", [])),
    }
    
    return diagnostics_data