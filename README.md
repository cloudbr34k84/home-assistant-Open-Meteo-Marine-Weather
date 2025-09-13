# Marine Weather Sensor Integration for Home Assistant

## Overview

This custom integration fetches marine weather data from the [Open-Meteo Marine API](https://marine-api.open-meteo.com/v1/marine) and exposes it in Home Assistant as sensors.
It provides current wave and swell conditions for user-defined locations.

## Features

* **Current Marine Weather Data:** Wave height, swell height, direction, and period.
* **Compass Conversion:** Converts numeric directions (degrees) to compass points (e.g., N, NE, SW).
* **Multiple Locations:** Define as many surf spots as needed in YAML.
* **Configurable Timezone:** Each location can use its own IANA timezone string.
* **Throttled Updates:** API requests limited to every 30 minutes.
* **Error Handling:** Logs HTTP, request, or JSON errors to Home Assistant log.

---

## Installation

1. **Copy files to `custom_components`**

   * Place the entire `marine_weather` folder (including `__init__.py`, `sensor.py`, `const.py`, `manifest.json`, and `logo.png`) under:

     ```
     <config>/custom_components/marine_weather/
     ```

2. **Check required files**

   * Ensure `const.py` is present. This file defines `DOMAIN` and `API_URL`.
   * Without it, the integration will fail to load.

3. **Configure sensors (two options)**

### Option 1: Inline in `configuration.yaml`

Add the following block directly under `sensor:`:

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

### Option 2: Split into separate files

If you manage sensors in their own YAML files (e.g., `sensors/marine_weather.yaml`), include this in your `configuration.yaml`:

```yaml
sensor: !include_dir_merge_list sensors
```

Then create `sensors/marine_weather.yaml` with:

```yaml
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

4. **Restart Home Assistant**

   * Restart to load the new integration and apply configuration.

---

## Usage

* Each location creates one entity in the format:

  ```
  <Location Name> Current
  ```

  Example: `Alexandra Headlands Current`

* Attributes include:

  * `swell_wave_height` (m)
  * `swell_wave_direction` (° and compass)
  * `swell_wave_period` (s)
  * `swell_wave_peak_period` (s)
  * `wave_height` (m)
  * `wave_direction` (° and compass)
  * `timezone` (matches configured timezone)
  * `models` (best\_match)

---

## Limitations

* **UI setup not supported.** You must use YAML configuration.
* **Forecast sensors are not implemented.** Only “current” data is available.

---

## Troubleshooting

* **Error: No module named `custom_components.marine_weather.const`**
  → Ensure `const.py` exists in the same folder as `sensor.py`.
* **Wrong timezone in attributes**
  → Check that your YAML includes a valid IANA timezone string (e.g., `Europe/Madrid`).
* **Entities not showing**
  → Verify YAML syntax, run “Check Configuration” in Developer Tools, then restart Home Assistant.

---

## Support

* Post issues or feature requests on the [GitHub repository](https://github.com/cloudbr34k84/Open-Meteo-Marine-Weather).

---
