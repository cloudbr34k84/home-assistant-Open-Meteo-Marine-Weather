# Open-Meteo Marine Weather

Marine weather conditions from the free [Open-Meteo Marine API](https://marine-api.open-meteo.com/v1/marine) — wave, swell, and wind-wave height, direction, and period, plus a 7-day and 24-hour forecast. No API key required.

## Requirements

- Home Assistant 2024.4 or later
- HACS installed

## Features

- Configured entirely through the UI — no YAML
- One device per location, with up to 13 individual sensors (wave/swell/wind-wave height, direction, period)
- A confirm step at setup shows each sensor's live value so you can skip any that don't apply to your location
- 7-day daily forecast and 24-hour hourly forecast as sensor attributes
- All sensors for a location share a single coordinator poll every 30 minutes
- Any number of locations supported

## Configuration

1. **Settings → Devices & Services → + Add Integration** → search **Open-Meteo Marine Weather**
2. Enter a name and coordinates (defaults to your Home Assistant location)
3. Choose which sensors to add from the live preview

Repeat for each additional location.

For full details, troubleshooting, and forecast attribute examples, see the [README](https://github.com/cloudbr34k84/home-assistant-Open-Meteo-Marine-Weather).

---
