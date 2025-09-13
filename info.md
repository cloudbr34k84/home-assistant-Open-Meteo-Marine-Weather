# Open Meteo Marine Weather

This custom integration provides marine weather conditions from the [Open-Meteo Marine API](https://marine-api.open-meteo.com/v1/marine).

## Requirements
- Home Assistant 2023.12 or later
- HACS installed (if using HACS option)

## Features

* Current swell and wave height, direction, and period
* Peak period tracking for swell and waves
* Compass direction conversion (degrees → compass points)
* Multiple user-defined locations (via YAML)
* Configurable timezone per location
* Automatic updates every 30 minutes
* No API key required (free public API)

## Configuration

Add locations in `configuration.yaml` (or split YAML files):

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

## Important Notes

* YAML configuration is required (no UI config flow).
* Ensure `const.py` is present in `custom_components/marine_weather/`.
* Restart Home Assistant after adding or changing locations.

For full installation steps and troubleshooting, see the [README](https://github.com/cloudbr34k84/Open-Meteo-Marine-Weather).

---