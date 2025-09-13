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

## Attribute Descriptions

Here’s a summary of what each attribute means and how they are used to understand surfing conditions:

### 1. **Wave Height (in meters)**
   - **Meaning**: Wave height measures the vertical distance between the trough (lowest point) and crest (highest point) of a wave.
   - **Usage**: It indicates the size of the waves in the ocean. Larger wave heights are typically preferred by more experienced surfers, while smaller wave heights may be more suitable for beginners. It’s a key factor in determining surfability and the potential challenge of the surf conditions.

### 2. **Wave Direction (in degrees and compass points)**
   - **Meaning**: Wave direction represents the direction from which the waves are coming. It is measured in degrees relative to true north and is often converted into compass points (e.g., N, NE, E, etc.).
   - **Usage**: Knowing the wave direction helps surfers determine the best spots to catch waves based on the coastline’s orientation and local geography. For example, a beach facing east will have better waves when the wave direction is from the east.

### 3. **Wave Period (in seconds)**
   - **Meaning**: The wave period is the time it takes for two successive wave crests to pass a fixed point, measured in seconds.
   - **Usage**: A longer wave period generally indicates more powerful, well-formed waves with more energy, which are preferred for surfing. Shorter periods often result in choppy conditions with less powerful waves.

### 4. **Swell Wave Height (in meters)**
   - **Meaning**: Swell wave height measures the size of waves generated by distant weather systems, rather than local winds. Swells typically produce more uniform and organized waves.
   - **Usage**: Swell wave height is critical for predicting the quality and size of waves at surf spots. Higher swell wave heights usually mean larger and more consistent waves, ideal for surfing.

### 5. **Swell Wave Direction (in degrees and compass points)**
   - **Meaning**: This indicates the direction from which the swell is arriving, measured in degrees or compass points.
   - **Usage**: Similar to general wave direction, swell wave direction helps surfers choose the right spots based on how the swell will interact with the coastline. Different swell directions can significantly affect wave quality and shape at different beaches.

### 6. **Swell Wave Period (in seconds)**
   - **Meaning**: This is the time interval between consecutive swell wave crests.
   - **Usage**: Longer swell periods usually mean the waves are more powerful and have traveled further, leading to better surfing conditions. Swells with longer periods tend to produce cleaner, more rideable waves.

### 7. **Wind Wave Height (in meters)**
   - **Meaning**: Wind wave height refers to the size of waves generated by local winds.
   - **Usage**: Local wind waves can create choppy and less predictable conditions, especially if they’re from a different direction than the swell. Surfers prefer conditions where wind wave height is low compared to swell wave height, as this typically results in cleaner waves.

### 8. **Wind Wave Direction (in degrees and compass points)**
   - **Meaning**: This shows the direction from which local wind waves are coming, measured in degrees or compass points.
   - **Usage**: Understanding wind wave direction is important for assessing how the wind will affect the surf. Onshore wind (wind blowing from the sea towards the land) usually creates choppy conditions, while offshore wind (wind blowing from the land towards the sea) can help create cleaner, more hollow waves.

### 9. **Wind Wave Period (in seconds)**
   - **Meaning**: This measures the time between successive wind-driven waves.
   - **Usage**: A shorter wind wave period usually means choppier surf conditions. Longer wind wave periods can indicate that the waves are better spaced and less chaotic, but typically, wind waves are less desirable compared to swells.

### **Overall Application:**
Surfers use this data to evaluate the potential quality of the waves and decide when and where to surf. Ideal conditions typically involve a good swell wave height with a long period, favorable wave direction relative to the beach, and minimal interference from local wind waves.

![Swell-vs-Wave](https://github.com/user-attachments/assets/fe33e670-4913-402a-8bba-072339a76e65)

---

This README provides a comprehensive guide for setting up and using the Marine Weather Sensor integration in Home Assistant, from installation to customization and usage.