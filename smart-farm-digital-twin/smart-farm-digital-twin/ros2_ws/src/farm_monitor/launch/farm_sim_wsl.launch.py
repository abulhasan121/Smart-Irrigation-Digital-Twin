#!/usr/bin/env python3
"""
farm_sim_wsl.launch.py
Launch file for the Smart Farm Digital Twin in WSL2 mode.
Starts the sensor simulator and irrigation controller nodes.

Author: Shah Md Abul Hasan, University of Georgia
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    drift_arg = DeclareLaunchArgument('drift_mul', default_value='0.3',
        description='Moisture drift multiplier (lower = slower drying)')

    return LaunchDescription([
        drift_arg,
        LogInfo(msg=[
            '\n',
            '=' * 58, '\n',
            '  SMART FARM DIGITAL TWIN\n',
            '  Nodes: sensor_simulator, irrigation_controller\n',
            '  Monitor: ros2 topic echo /farm/irrigation_status\n',
            '=' * 58,
        ]),
        Node(
            package='farm_monitor',
            executable='sensor_simulator',
            name='sensor_simulator',
            parameters=[{'drift_mul': LaunchConfiguration('drift_mul')}],
            output='screen',
        ),
        Node(
            package='farm_monitor',
            executable='irrigation_controller',
            name='irrigation_controller',
            output='screen',
        ),
    ])
