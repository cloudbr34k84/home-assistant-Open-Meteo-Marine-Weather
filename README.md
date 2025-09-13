# Marine Weather Sensor Integration for Home Assistant

## Quick Start

1. Copy the folder `marine_weather` into:

   ```
   <config>/custom_components/
   ```

2. Add this to your sensor configuration (see “Configuration” section for details):

   ```yaml
   - platform: marine_weather
     locations:
       - name: "My Beach"
         latitude: 36.0969
         longitude: -5.8147
         timezone: "Europe/Madrid"
   ```

3. Restart Home Assistant.
   → You’ll see a sensor called `My Beach Current` with attributes for wave and swell data.

---

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

Then in `sensors/marine_weather.yaml`:

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

## FAQ

**Q: Why can’t I add this integration from the UI?**
A: This integration does not include a `config_flow.py` file. It only supports YAML configuration.

**Q: My timezone shows as `Australia/Sydney`, but I’m in Europe. Why?**
A: Older versions hardcoded `Australia/Sydney`. The current version lets you set `timezone:` per location in YAML. Use a valid [IANA timezone string](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) like `Europe/Madrid`.

**Q: I get `No module named const` errors.**
A: Make sure `const.py` exists in `custom_components/marine_weather/`. If missing, copy it from the repository or recreate it:

```python
DOMAIN = "marine_weather"
API_URL = "https://marine-api.open-meteo.com/v1/marine"
```

**Q: Can I define locations in multiple YAML files?**
A: Yes. If you use `!include_dir_merge_list sensors`, you can keep `marine_weather.yaml` separate, just like any other integration.

---

## Support

* Post issues or feature requests on the [GitHub repository](https://github.com/cloudbr34k84/Open-Meteo-Marine-Weather).

---