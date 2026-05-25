# System Architecture

## Component Overview

The Smart Farm Digital Twin is built as a modular ROS 2 system. Each component communicates via
named topics using a lightweight BEST_EFFORT QoS profile tuned for real-time sensor data.

## Data Flow

```
sensor_simulator
      |
      | /farm/zoneX/soil_moisture  (Float32)
      | /farm/zoneX/temperature    (Float32)
      | /farm/zoneX/humidity       (Float32)
      |
      v
irrigation_controller
      |
      | /farm/zoneX/irrigation_cmd  (String: ON|OFF)
      | /farm/irrigation_status     (String: JSON)
      |
      +-----> water_spray_effect.py  (Gazebo particle FX)
      |
      +-----> smart_farm_dashboard.py (Flask WebSocket)
```

## Irrigation Decision Model

The controller evaluates each zone independently on every moisture reading.

States:
- CRITICAL  (moisture < 20%) - irrigation ON immediately
- DRY       (moisture < 30%) - irrigation ON
- SUFFICIENT (moisture >= 33%) - irrigation OFF (hysteresis band)
- WET       (moisture >= 70%) - irrigation OFF

Environmental corrections reduce the effective threshold when:
- Air temperature exceeds 30 C (threshold -5%)
- Relative humidity drops below 40% (threshold -3%)

The 3% hysteresis band between DRY (30%) and SUFFICIENT (33%) prevents
rapid ON/OFF relay cycling when moisture is near the threshold.

## Sensor Simulation

The sensor simulator models three independent zones with:
- Evapotranspiration drift (configurable rate per zone)
- Diurnal temperature variation (sine curve over 24-hour period)
- Humidity inversely correlated with temperature
- Gaussian noise on all readings
- Immediate moisture boost when irrigation is active

## QoS Settings

All sensor topics use BEST_EFFORT reliability with KEEP_LAST (depth 5).
This reduces DDS memory overhead compared to RELIABLE delivery, which is
appropriate for sensor readings where occasional packet loss is acceptable.
