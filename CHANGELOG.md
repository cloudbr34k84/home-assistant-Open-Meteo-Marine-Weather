Here’s a clean `CHANGELOG.md` you can drop into your repo root. It gives you a professional starting point and aligns with HACS best practices.

---

# 📑 Changelog

All notable changes to this project will be documented here.
This project follows [Semantic Versioning](https://semver.org/) (vMAJOR.MINOR.PATCH).

---

## \[v1.0.0] — 2025-09-14

### 🎉 Initial Release

* First release of **Open-Meteo Marine Weather** integration for Home Assistant.
* Features included:

  * Current marine weather data (wave height, swell height, direction, period).
  * Compass conversion for directions (° → N, NE, SW, etc.).
  * Multiple location support via YAML.
  * Configurable timezone per location.
  * Throttled API updates (30 min).
  * Basic error handling and logging.
  * HACS compatibility (via custom repository).
* Known limitations:

  * No UI setup (YAML-only).
  * Forecast entities not yet implemented.
  * Visualization (Marine Wave Card) coming in a future release.

---

## \[Unreleased]

### 🚧 Planned

* UI config flow & options flow.
* Forecast sensors (3h, 6h, 24h).
* Tide entity merge.
* Marine Wave Card visualization.

---