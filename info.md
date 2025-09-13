
# Open Meteo Marine Weather

This integration provides live marine weather conditions from the [Open-Meteo Marine API](https://marine-api.open-meteo.com/v1/marine).

## 🌊 Features

* Current swell and wave height, direction, and period
* Peak period tracking for swell and waves
* Compass direction conversion (degrees → N, NE, etc.)
* Support for multiple user-defined surf locations
* Configurable timezone per location
* Auto-updating sensor data (every 30 minutes)
* No API key required (free public API)

## 📍 Configuration

Define your own locations in `configuration.yaml` (or split YAML). Example:

```yaml
sensor:
  - platform: marine_weather
    locations:
      - name: "Alexandra Headlands"
        latitude: -26.6715
        longitude: 153.1006
        timezone: "Australia/Brisbane"
      - name: "Kings Beach"
        latitude: -26.8017
        longitude: 153.1426
        timezone: "Australia/Brisbane"
```

## ℹ️ Notes

* This integration currently **requires YAML configuration** (no UI config flow yet).
* `const.py` must be present in `custom_components/marine_weather`.
* Data is pulled directly from the Open-Meteo API — no authentication or keys are needed.
* Restart Home Assistant after adding or changing locations.

See the full README for installation instructions, advanced setup, and troubleshooting.

---