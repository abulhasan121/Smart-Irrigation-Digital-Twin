#!/bin/bash
# Quick launcher for the Smart Farm Digital Twin

source /opt/ros/jazzy/setup.bash
source "$(dirname "$0")/../ros2_ws/install/setup.bash"

echo "Starting sensor simulator..."
ros2 run farm_monitor sensor_simulator --ros-args -p drift_mul:=0.3 &

echo "Starting irrigation controller..."
sleep 2
ros2 run farm_monitor irrigation_controller &

echo ""
echo "All nodes running."
echo "Monitor: ros2 topic echo /farm/irrigation_status"
echo "Press Ctrl+C to stop."
wait
