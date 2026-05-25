#!/usr/bin/env python3
"""
sensor_simulator.py
Smart Farm Digital Twin - Sensor Simulator Node

Simulates soil moisture, temperature, and humidity sensors for three
farm zones. Moisture drifts downward over time (evapotranspiration)
and rises when irrigation is active, creating a realistic closed loop.

Topics Published per zone X in {1,2,3}:
  /farm/zoneX/soil_moisture   std_msgs/Float32
  /farm/zoneX/temperature     std_msgs/Float32
  /farm/zoneX/humidity        std_msgs/Float32

Topics Subscribed per zone X in {1,2,3}:
  /farm/zoneX/irrigation_cmd  std_msgs/String

Author: Shah Md Abul Hasan, University of Georgia
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import math, random, time

SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=5
)

ZONE_CONFIG = {
    1: {"drift": 0.8, "temp_base": 21.0, "hum_base": 65.0},
    2: {"drift": 1.0, "temp_base": 24.0, "hum_base": 53.0},
    3: {"drift": 0.7, "temp_base": 18.0, "hum_base": 70.0},
}

class SensorSimulatorNode(Node):
    ZONES = [1, 2, 3]
    PUBLISH_HZ = 1.0
    MOISTURE_BOOST = 7.5
    MOISTURE_FLOOR = 5.0
    MOISTURE_CEIL  = 95.0

    def __init__(self):
        super().__init__('sensor_simulator')
        self.declare_parameter('drift_mul', 1.0)
        self.drift_mul = self.get_parameter('drift_mul').value
        self._moisture   = {z: random.uniform(30.0, 50.0) for z in self.ZONES}
        self._irrigation = {z: False for z in self.ZONES}
        self._start_time = time.time()
        self._pub_moisture = {}
        self._pub_temp     = {}
        self._pub_humidity = {}
        for z in self.ZONES:
            p = f"/farm/zone{z}"
            self._pub_moisture[z] = self.create_publisher(Float32, f"{p}/soil_moisture", SENSOR_QOS)
            self._pub_temp[z]     = self.create_publisher(Float32, f"{p}/temperature",   SENSOR_QOS)
            self._pub_humidity[z] = self.create_publisher(Float32, f"{p}/humidity",       SENSOR_QOS)
            self.create_subscription(String, f"{p}/irrigation_cmd",
                lambda msg, z=z: self._cb_irr(msg, z), SENSOR_QOS)
        self.create_timer(1.0 / self.PUBLISH_HZ, self._publish)
        self.get_logger().info(f"[SensorSim] Started — {self.PUBLISH_HZ} Hz, zones {self.ZONES}")

    def _cb_irr(self, msg, zone):
        self._irrigation[zone] = msg.data.strip().upper() == "ON"

    def _publish(self):
        elapsed = time.time() - self._start_time
        lines = []
        for z in self.ZONES:
            cfg   = ZONE_CONFIG[z]
            drift = cfg["drift"] * self.drift_mul * 0.1
            if self._irrigation[z]:
                self._moisture[z] = min(self._moisture[z] + self.MOISTURE_BOOST, self.MOISTURE_CEIL)
            else:
                self._moisture[z] = max(self._moisture[z] - drift, self.MOISTURE_FLOOR)
            m = max(self.MOISTURE_FLOOR, min(self.MOISTURE_CEIL, self._moisture[z] + random.gauss(0, 0.4)))
            hour = (elapsed / 3600.0) % 24
            t = cfg["temp_base"] + 3.0 * math.sin(2 * math.pi * (hour - 14) / 24) + random.gauss(0, 0.3)
            h = max(30.0, min(90.0, cfg["hum_base"] - 0.3 * (t - cfg["temp_base"]) + random.gauss(0, 0.5)))
            self._pub_moisture[z].publish(Float32(data=float(m)))
            self._pub_temp[z].publish(Float32(data=float(t)))
            self._pub_humidity[z].publish(Float32(data=float(h)))
            lines.append(f"  Zone {z}: moisture={m:.1f}%  temp={t:.1f}C  hum={h:.1f}%  irr={'ON' if self._irrigation[z] else 'OFF'}")
        if int(elapsed) % 10 == 0:
            self.get_logger().info("[SensorSim] Readings:\n" + "\n".join(lines))

def main(args=None):
    rclpy.init(args=args)
    node = SensorSimulatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
