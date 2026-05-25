from setuptools import setup
import os
from glob import glob

package_name = 'farm_monitor'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Shah Md Abul Hasan',
    maintainer_email='your_email@uga.edu',
    description='Smart Farm Digital Twin - ROS 2 sensor and irrigation nodes',
    license='MIT',
    entry_points={
        'console_scripts': [
            'sensor_simulator    = farm_monitor.sensor_simulator:main',
            'irrigation_controller = farm_monitor.irrigation_controller:main',
        ],
    },
)
