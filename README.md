# Smart Farm Gazebo Digital Twin

A prototype smart farm simulation that demonstrates how soil moisture sensing and automated irrigation can be modelled within a digital twin framework. The system uses ROS 2 Jazzy and Gazebo Harmonic to simulate a virtual agricultural environment with sensor nodes, irrigation infrastructure, and real-time decision logic.

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue?logo=ros)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-purple)
![Python](https://img.shields.io/badge/Python-3.12-green?logo=python)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Overview

This prototype explores how a digital twin can be used to model and test smart irrigation logic before deploying it on real hardware. The simulation runs a closed-loop pipeline where virtual sensors feed data into an irrigation controller, which makes real-time ON/OFF decisions based on soil moisture thresholds. The results are visualised in both a 3D Gazebo environment and a live web dashboard.

The project covers:

- Procedurally generated 3D maize field with realistic terrain and crop models
- Simulated soil moisture, temperature, and humidity sensors across three independent farm zones
- Adaptive irrigation controller with multi-threshold decision logic and hysteresis
- Water spray particle effects in Gazebo triggered by irrigation events
- Live web dashboard with real-time charts and zone status indicators
- Full ROS 2 pub/sub architecture with tuned QoS settings

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ROS 2 Jazzy (Ubuntu 24.04 WSL2)           │
│                                                             │
│  ┌──────────────────┐        ┌───────────────────────────┐  │
│  │ sensor_simulator  │───────▶│  irrigation_controller    │  │
│  │                  │        │                           │  │
│  │ /farm/zoneX/     │        │ /farm/zoneX/              │  │
│  │  soil_moisture   │        │  irrigation_cmd           │  │
│  │  temperature     │        │ /farm/irrigation_status   │  │
│  │  humidity        │        └─────────────┬─────────────┘  │
│  └──────────────────┘                      │                │
│                                            │                │
│  ┌──────────────────┐        ┌─────────────▼─────────────┐  │
│  │ water_spray_     │◀───────│  Gazebo Harmonic           │  │
│  │ effect.py        │        │  virtual_maize_field       │  │
│  │                  │        │  sensor poles + pumps      │  │
│  └──────────────────┘        └───────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Flask + SocketIO Dashboard  →  http://localhost:5000  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| Realistic 3D farm | Procedurally generated maize field with heightmap terrain via Gazebo Harmonic |
| Multi-zone sensing | 3 independent zones each with soil moisture, temperature, and humidity simulation |
| Adaptive irrigation | Multi-threshold controller with CRITICAL / DRY / SUFFICIENT / WET states and 3% hysteresis |
| Water spray effects | Blue droplet particle effects spawned in Gazebo when irrigation activates |
| Live dashboard | Web dashboard with real-time moisture charts and zone irrigation status |
| ROS 2 topics | Full pub/sub architecture with BEST_EFFORT QoS for low-latency streaming |
| WSL2 optimised | Tuned for 8 GB RAM systems; no GPU required; runs with WSLg display |

---

## System Requirements

| Component | Requirement |
|---|---|
| OS | Windows 10/11 with WSL2 |
| WSL distro | Ubuntu 24.04 LTS |
| RAM | 8 GB minimum (15 GB recommended) |
| Disk | 10 GB free |
| Display | WSLg (built into Windows 11 / Windows 10 22H2+) |

---

## Installation

### 1. Set up Ubuntu 24.04 on WSL2

```powershell
# In PowerShell (Admin)
wsl --install -d Ubuntu-24.04
wsl --set-default Ubuntu-24.04
```

### 2. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-farm-digital-twin.git
cd smart-farm-digital-twin
```

### 3. Run the installer

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This installs ROS 2 Jazzy, Gazebo Harmonic, Python dependencies, and builds the workspace. Expect around 10 minutes on first run.

### 4. Build the virtual maize field

```bash
mkdir -p ~/ros2_farm_ws/src
cp -r ~/virtual_maize_field ~/ros2_farm_ws/src/
cd ~/ros2_farm_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
ros2 run virtual_maize_field generate_world
```

### 5. Install dashboard dependencies

```bash
pip install flask flask-socketio --break-system-packages
```

---

## Running the System

Open four terminals, each starting with:

```bash
wsl -d Ubuntu-24.04 --cd ~
```

**Terminal 1 — Gazebo simulation**

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_farm_ws/install/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:~/ros2_farm_ws/install/virtual_maize_field/share/virtual_maize_field/models
gz sim ~/.ros/virtual_maize_field/generated.world
```

**Terminal 2 — Sensor and irrigation nodes**

```bash
source /opt/ros/jazzy/setup.bash
source ~/smart-farm-digital-twin/ros2_ws/install/setup.bash
ros2 run farm_monitor sensor_simulator --ros-args -p drift_mul:=0.3 &
sleep 2
ros2 run farm_monitor irrigation_controller
```

**Terminal 3 — Water spray effects**

```bash
source /opt/ros/jazzy/setup.bash
source ~/smart-farm-digital-twin/ros2_ws/install/setup.bash
python3 ~/water_spray_effect.py
```

**Terminal 4 — Web dashboard**

```bash
source /opt/ros/jazzy/setup.bash
source ~/smart-farm-digital-twin/ros2_ws/install/setup.bash
python3 ~/smart_farm_dashboard.py
```

Open **http://localhost:5000** in your Windows browser to access the dashboard.

---

## ROS 2 Topics

| Topic | Type | Description |
|---|---|---|
| `/farm/zoneX/soil_moisture` | `std_msgs/Float32` | Soil moisture percentage (0-100) |
| `/farm/zoneX/temperature` | `std_msgs/Float32` | Air temperature in Celsius |
| `/farm/zoneX/humidity` | `std_msgs/Float32` | Relative humidity percentage |
| `/farm/zoneX/irrigation_cmd` | `std_msgs/String` | Irrigation command: ON or OFF |
| `/farm/irrigation_status` | `std_msgs/String` | JSON status report for all zones |

Monitor live data:

```bash
ros2 topic echo /farm/irrigation_status
ros2 topic list
```

---

## Irrigation Logic

The controller applies a multi-threshold model independently to each zone:

```
soil_moisture < 20%   →  CRITICAL   →  irrigation ON  (immediate response)
soil_moisture < 30%   →  DRY        →  irrigation ON
soil_moisture >= 33%  →  SUFFICIENT →  irrigation OFF  (3% hysteresis band)
soil_moisture >= 70%  →  WET        →  irrigation OFF  (over-watering guard)

Environmental adjustments:
  temperature > 30 C  →  effective threshold reduced by 5%
  humidity < 40%      →  effective threshold reduced by 3%
```

The hysteresis band prevents rapid ON/OFF cycling when moisture is near the threshold.

---

## Repository Structure

```
smart-farm-digital-twin/
├── ros2_ws/
│   └── src/
│       └── farm_monitor/
│           ├── farm_monitor/
│           │   ├── sensor_simulator.py
│           │   ├── irrigation_controller.py
│           │   └── rviz_marker_publisher.py
│           └── launch/
│               ├── farm_sim_wsl.launch.py
│               └── rviz_farm.launch.py
├── worlds/
│   ├── smart_farm.sdf
│   └── smart_farm.urdf
├── scripts/
│   ├── install.sh
│   └── run.sh
├── water_spray_effect.py
├── smart_farm_dashboard.py
└── README.md
```

---

## Future Work

- Integration with physical IoT sensors via MQTT bridge
- Machine learning based irrigation prediction using historical sensor data
- Weather API integration for evapotranspiration modelling
- Autonomous mobile robot for in-field crop inspection
- Drone-based aerial monitoring with ROS 2 navigation stack
- Multi-zone optimisation using reinforcement learning
- Synchronisation with real farm GPS coordinates for deployment

---

## Technologies

| Technology | Version | Purpose |
|---|---|---|
| ROS 2 Jazzy | LTS 2024 | Robot middleware and communication |
| Gazebo Harmonic | Latest | 3D physics simulation |
| Python | 3.12 | Node logic and dashboard backend |
| Flask + SocketIO | Latest | Real-time web dashboard |
| virtual_maize_field | GitHub | Procedural crop field generation |
| Gazebo Fuel | OpenRobotics | Realistic 3D model assets |
| Ubuntu 24.04 | Noble | Host operating system via WSL2 |

---

## Author

Shah Md Abul Hasan
University of Georgia (UGA)

---

## License

MIT License
