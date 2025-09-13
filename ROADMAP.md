# 🌊 Marine Weather Integration — Roadmap

This file outlines planned features, improvements, and long-term vision for the **Open Meteo Marine Weather** integration.
The roadmap is aspirational — not all features are guaranteed, but it reflects the intended direction.

---

## Phase 1 — Quality & Compliance (short-term)

**Goal:** Get the integration accepted into HACS and ensure a solid foundation.

* **HACS Approval Readiness**

  * Repo structure must follow HACS rules (`custom_components/marine_weather`, `brands/marine_weather`, `hacs.json`, `manifest.json`).
  * Ensure `info.md`, `README.md`, and `LICENSE` are present and accurate.
* **Error Handling**

  * Gracefully handle missing or partial API data.
  * Show `"N/A"` or placeholder values instead of empty attributes.
  * Log structured warnings in HA’s system log.
* **Unit Tests**

  * Add pytest coverage for:

    * `degrees_to_compass` utility.
    * Attribute formatting functions.
    * Error/exception handling.

---

## Phase 2 — Usability & Config (medium-term)

**Goal:** Improve user experience by reducing reliance on YAML and making the integration easier to manage.

* **Config Flow (UI Setup)**

  * Add support for HA’s `config_flow.py`.
  * Users can add integration from **Settings → Devices & Services**.
* **Options Flow**

  * Allow editing of locations and timezones via the UI.
  * Support multiple spots without restarting HA.
* **Model Selection**

  * Open-Meteo supports different models (ECMWF, GFS, ICON).
  * Let users select which model to use in config.
* **Diagnostics Expansion**

  * Extend `diagnostics.py` to show:

    * Last API payload summary.
    * API call frequency.
    * Error count / last error reason.

---

## Phase 3 — Data Expansion (medium/long-term)

**Goal:** Provide richer marine weather coverage.

* **Forecast Entities**

  * Add 3h, 6h, and 24h forecast sensors.
  * Entities: `wave_height_forecast_3h`, `swell_period_forecast_6h`, etc.
* **Wind & Weather**

  * Expose wind wave attributes (height, direction, period).
  * Optionally integrate with HA’s `weather` entities for combined surf/wind dashboards.
* **Separate Sensors**

  * Current approach: one sensor with many attributes.
  * Planned: break attributes into dedicated sensors (e.g. `sensor.swell_period`, `sensor.wave_height`).
  * Improves Lovelace graphs and history tracking.
* **Tide Integration**

  * Detect local tide entity (e.g. `sensor.local_tide`).
  * Merge into Lovelace card display.
  * Support combined surf + tide dashboards.

---

## Phase 4 — Visualization & UX (long-term)

**Goal:** Deliver a full surf dashboard experience inside Home Assistant by combining marine weather data, tide info, and wind conditions into a dedicated Lovelace card.

* **Marine Wave Card (Core Feature)**

  * Custom Lovelace card (`custom:marine-wave-card`) that visualizes swell, waves, and wind in a surf-report style interface.
  * Features include:

    * Surf height bars (color-coded).
    * Swell period overlays (line chart for consistency/quality).
    * Wind arrows (direction + speed/gusts).
    * 24-hour rolling history with 6-hour ticks.
    * Compact, surf-forecast-style presentation.

* **Wave + Tide Chart Overlay**

  * Optionally combine tide entity data with wave forecasts in the same chart (stacked or dual-axis).

* **Directional Icons**

  * Graphical compass arrows for swell/wave direction.

* **Surf-Friendly Summary**

  * Auto-generate plain-text conditions like:
    *“3ft clean E swell, 12s period. Low tide 9:45am, rising.”*

* **Lovelace Card Bundle**

  * Publish the Marine Wave Card to HACS as a standalone frontend package.
  * Provide presets that combine:

    * Marine Weather integration data.
    * Local tide entity.
    * Wind/weather entities.

* **Preset Dashboards**

  * Ready-made “Surf Spot” dashboard templates (e.g., Sunshine Coast example with Alexandra Headlands, Kings Beach, Moffat Beach).

---

## Phase 5 — Advanced Features (future ideas)

**Goal:** Extend integration for power users and automation.

* **REST/Coordinator Refactor**

  * Migrate API fetch into a `DataUpdateCoordinator`.
  * Allow reuse by `sensor`, `binary_sensor`, `weather`, and other HA platforms.
* **Adaptive Polling**

  * Faster update intervals during surf hours.
  * Slower updates overnight.
* **Alerts & Automations**

  * Binary sensors or events, e.g.:

    * `binary_sensor.big_swell_alert` (swell > 2m).
    * `binary_sensor.tide_dropping_fast`.
* **External API Expansion**

  * Combine with other oceanographic APIs (NOAA, BOM, Surfline).
  * Offer hybrid data sources for redundancy.

---

## Contribution Guidelines

* **Issues & Ideas** → Use GitHub Issues for bug reports, feature requests, or discussion.
* **Pull Requests** → Contributions welcome, especially for config flow, forecast support, and Lovelace card development.
* **Testing** → Please include sample config and logs when reporting issues.

---

📌 This roadmap will evolve. The focus is **incremental quality improvements first**, then **usability**, followed by **data expansion and visualization**.

---
