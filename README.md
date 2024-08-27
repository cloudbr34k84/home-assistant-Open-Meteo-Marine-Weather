
# Marine Weather Sensor Integration for Home Assistant

## Overview

This integration provides marine weather data for specific surf locations, creating sensors that track current conditions and forecasted attributes such as wave height, wave direction, swell wave height, and more. The integration uses the Marine Weather API from open-meteo.com and is designed for Home Assistant.

## Features

- **Current Marine Weather Sensors:** Provides real-time data for wave height, wave direction, swell wave height, and more at specific surf locations.
- **Forecast Sensors:** Offers detailed daily forecasts for various marine weather attributes up to five days in advance.
- **Customizable Locations:** Hardcoded to specific surf spots, but can be modified to include other locations by changing the latitude and longitude in the code.
- **Compass Direction Conversion:** Converts wave and wind directions from degrees to compass directions (e.g., N, NE, E, etc.).

## Installation

1. **Download the Code:**
   - Copy the `sensor.py` file to your Home Assistant's custom components folder. If you don't have a custom components folder, create one under `<config>/custom_components/marine_weather/`.

2. **Specify Locations:**
   - In the `sensor.py` file, locate the `LOCATIONS` list. Here, you need to provide the latitude, longitude, and a descriptive name for each location you want to track.
   - Example configuration:
     ```python
     LOCATIONS = [
         {"latitude": -26.6715, "longitude": 153.1006, "name": "Alexandra Headlands Surf Location"},
         {"latitude": -26.8017, "longitude": 153.1426, "name": "Kings Beach Surf Location"},
         {"latitude": -26.7905, "longitude": 153.1400, "name": "Moffat Beach Surf Location"},
     ]
     ```
   - Modify these values to match the specific locations you wish to monitor. Ensure that the latitude and longitude are accurate for each spot.

3. **Deploy the Integration:**
   - After updating the `LOCATIONS` in the `sensor.py` file, you simply need to save the changes and ensure that the `sensor.py` file is correctly placed in your Home Assistant custom components directory (typically `<config>/custom_components/marine_weather/`).
   - Home Assistant will automatically recognize the integration during startup, and you should see the new sensors in your entities list.

4. **Restart Home Assistant:**
   - Restart your Home Assistant instance to apply the changes. The new sensors will be available after the restart.

## Usage

### Sensors Created

#### Current Conditions Sensors
These sensors provide real-time data on the current marine conditions. Each sensor is named based on the location, e.g., `Alexandra Headlands Surf Location Current`.

- **wave_height:** The height of the waves in meters.
- **wave_direction:** The direction of the waves in degrees and compass points.
- **swell_wave_height:** The height of the swell waves in meters.
- **swell_wave_direction:** The direction of the swell waves in degrees and compass points.

#### Forecast Sensors
For each location, the integration creates forecast sensors for up to five days. Each forecast day has sensors for attributes such as:

- **Wave Height (in meters)**
- **Wave Direction (in degrees and compass points)**
- **Wave Period (in seconds)**
- **Swell Wave Height (in meters)**
- **Swell Wave Direction (in degrees and compass points)**
- **Swell Wave Period (in seconds)**
- **Wind Wave Height (in meters)**
- **Wind Wave Direction (in degrees and compass points)**
- **Wind Wave Period (in seconds)**

### Sensor Naming Convention

- **Current Condition Sensors:**
  - `<Location Name> Current`
  - Example: `Alexandra Headlands Surf Location Current`

- **Forecast Sensors:**
  - `<Location Name> Day <Day Number> <Attribute Name>`
  - Example: `Kings Beach Surf Location Day 1 Wave Height`

### Throttling

To avoid overwhelming the API, updates are throttled to occur no more than once every 30 minutes.

### Error Handling

The integration logs errors such as HTTP errors, request exceptions, and JSON decoding errors, ensuring any issues with data fetching are captured.

## Extending the Integration

To add more locations or modify the attributes tracked, edit the `LOCATIONS` array or the `attributes` array in the `sensor.py` file. Be sure to maintain the correct latitude, longitude, and attribute names as per the Marine Weather API documentation.

## Support

For issues or feature requests, please consult the Home Assistant community forums or the integration's GitHub repository.

---

This README provides a comprehensive guide for setting up and using the Marine Weather Sensor integration in Home Assistant, from installation to customization and usage.
