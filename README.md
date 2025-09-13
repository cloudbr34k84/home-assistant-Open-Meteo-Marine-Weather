# Marine Weather Sensor Integration for Home Assistant

## Overview

This custom integration fetches marine weather data from the [Open-Meteo Marine API](https://marine-api.open-meteo.com/v1/marine) and exposes it in Home Assistant as sensors.
It provides current wave and swell conditions for user-defined locations.

## Features

* **Current Marine Weather Data:** Wave height, swell height, direction, and period
* **Compass Conversion:** Converts degrees into compass points (e.g., N, NE, SW)
* **Multiple Locations:** Define as many surf spots as needed in YAML
* **Configurable Timezone:** Each location can use its own IANA timezone string
* **Throttled Updates:** API requests limited to every 30 minutes
* **Error Handling:** Logs HTTP, request, or JSON errors to the Home Assistant log

---

## Installation

### Option 1: Manual install

Copy the entire `marine_weather` folder (including `__init__.py`, `sensor.py`, `const.py`, `manifest.json`, and `logo.png`) into:

```
<config>/custom_components/marine_weather/
```

### Option 2: Install via HACS (Custom Repository)

1. Go to **HACS → Integrations → Custom Repositories**
2. Add the repo:

   ```
   https://github.com/cloudbr34k84/Open-Meteo-Marine-Weather
   ```

   Type: **Integration**
3. Click **Add**
4. Search for **Open Meteo Marine Weather** in HACS and install
5. Restart Home Assistant

### Post-install check

* Ensure `const.py` is present. This file defines `DOMAIN` and `API_URL`
* Without it, the integration will fail to load

---

## Configuration

You can configure the integration inline or using split YAML files.

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

⚠️ Use this only if your `configuration.yaml` includes:

```yaml
sensor: !include_dir_merge_list sensors
```

Then create `sensors/marine_weather.yaml`:

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

Restart Home Assistant to apply changes.

---

## Usage

Each defined location creates one entity:

```
<Location Name> Current
```

Example: `Alexandra Headlands Current`

### Attributes include:

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

* **UI setup not supported.** YAML configuration only
* **Forecast sensors not implemented.** Only “current” data is available

---

## Troubleshooting

* **Error: `No module named custom_components.marine_weather.const`**
  → Ensure `const.py` exists in the same folder as `sensor.py`

* **Wrong timezone in attributes**
  → Check that your YAML includes a valid IANA timezone string (e.g., `Europe/Madrid`)

* **Entities not showing**
  → Verify YAML syntax, run *Check Configuration* in Developer Tools, then restart Home Assistant

---

## FAQ

**Q: Why can’t I add this integration from the UI?**
A: This integration does not include a config flow. It must be configured via YAML.

**Q: My timezone shows as `Australia/Sydney`, but I’m in Europe. Why?**
A: Use the `timezone:` option in YAML for each location. Use a valid IANA timezone (e.g., `Europe/Madrid`).

**Q: I get “No module named const”?**
A: Make sure `const.py` is inside `custom_components/marine_weather/`.

**Q: Can I define locations in multiple YAML files?**
A: Yes. Use `!include_dir_merge_list sensors` in `configuration.yaml` and create a separate `marine_weather.yaml`.

---

## Support

* Post issues or feature requests on the [GitHub repository](https://github.com/cloudbr34k84/Open-Meteo-Marine-Weather)

---
