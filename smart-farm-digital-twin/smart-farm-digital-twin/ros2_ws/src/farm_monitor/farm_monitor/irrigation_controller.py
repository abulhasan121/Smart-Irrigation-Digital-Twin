#!/usr/bin/env python3
"""
irrigation_controller.py
Smart Farm Digital Twin - Irrigation Controller Node

Subscribes to zone sensor topics and applies a multi-threshold
irrigation decision model. Publishes irrigation commands and a
consolidated JSON status report.

Decision logic per zone:
  CRITICAL  soil_moisture < 20%  -> irrigation ON  (immediate)
  DRY       soil_moisture < 30%  -> irrigation ON
  SUFFICIENT moisture >= 33%     -> irrigation OFF  (hysteresis)
  WET       moisture >= 70%      -> irrigation OFF  (over-water guard)

Author: Shah Md Abul Hasan, University of Georgia
"""

import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

THRESHOLD_CRITICAL = 20.0
THRESHOLD_DRY      = 30.0
THRESHOLD_WET      = 70.0
TEMP_HIGH          = 30.0
HUM_LOW            = 40.0
HYSTERESIS         = 3.0
STATUS_HZ          = 0.5

SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=5
)

class IrrigationControllerNode(Node):
    ZONES = [1, 2, 3]

    def __init__(self):
        super().__init__('irrigation_controller')
        self._moisture   = {z: None for z in self.ZONES}
        self._temp       = {z: None for z in self.ZONES}
        self._humidity   = {z: None for z in self.ZONES}
        self._irrigation = {z: False for z in self.ZONES}
        self._pub_cmd    = {}
        for z in self.ZONES:
            p = f"/farm/zone{z}"
            self.create_subscription(Float32, f"{p}/soil_moisture",
                lambda msg, z=z: self._cb_moisture(msg, z), SENSOR_QOS)
            self.create_subscription(Float32, f"{p}/temperature",
                lambda msg, z=z: self._cb_temp(msg, z), SENSOR_QOS)
            self.create_subscription(Float32, f"{p}/humidity",
                lambda msg, z=z: self._cb_humidity(msg, z), SENSOR_QOS)
            self._pub_cmd[z] = self.create_publisher(String, f"{p}/irrigation_cmd", SENSOR_QOS)
        self._pub_status = self.create_publisher(String, "/farm/irrigation_status", 10)
        self.create_timer(1.0 / STATUS_HZ, self._publish_status)
        self.get_logger().info(
            f"[IrrigationController] Node started | Zones: {self.ZONES} | "
            f"DryThreshold: {THRESHOLD_DRY}% | CriticalThreshold: {THRESHOLD_CRITICAL}%"
        )

    def _cb_moisture(self, msg, zone):
        m = msg.data
        self._moisture[zone] = m
        irr = self._irrigation[zone]
        t_eff = THRESHOLD_DRY
        if self._temp[zone] and self._temp[zone] > TEMP_HIGH:
            t_eff -= 5.0
        if self._humidity[zone] and self._humidity[zone] < HUM_LOW:
            t_eff -= 3.0
        t_suf = t_eff + HYSTERESIS
        if not irr:
            if m < THRESHOLD_CRITICAL:
                self._set_irrigation(zone, True, f"CRITICAL: moisture {m:.1f}% < {THRESHOLD_CRITICAL:.1f}%")
            elif m < t_eff:
                self._set_irrigation(zone, True, f"DRY: moisture {m:.1f}% < threshold {t_eff:.1f}%")
        else:
            if m >= THRESHOLD_WET:
                self._set_irrigation(zone, False, f"WET: moisture {m:.1f}% >= {THRESHOLD_WET:.1f}%")
            elif m >= t_suf:
                self._set_irrigation(zone, False, f"SUFFICIENT: moisture {m:.1f}% > {t_suf:.1f}%")

    def _cb_temp(self, msg, zone):
        self._temp[zone] = msg.data

    def _cb_humidity(self, msg, zone):
        self._humidity[zone] = msg.data

    def _set_irrigation(self, zone, state, reason):
        prev = self._irrigation[zone]
        if prev == state:
            return
        self._irrigation[zone] = state
        cmd = "ON" if state else "OFF"
        prev_str = "ON" if prev else "OFF"
        self.get_logger().info(f"[Zone {zone}] Irrigation {prev_str} -> {cmd} | {reason}")
        self._pub_cmd[zone].publish(String(data=cmd))

    def _publish_status(self):
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        zones_data = {}
        lines = []
        for z in self.ZONES:
            m = self._moisture[z]
            irr = "ON" if self._irrigation[z] else "OFF"
            m_str = f"{m:.1f}%" if m is not None else "N/A"
            icon = "🚨" if (m is not None and m < THRESHOLD_CRITICAL) else \
                   "💧" if (m is not None and m < THRESHOLD_DRY) else "✅"
            lines.append(f"  {icon} Zone {z}: moisture={m_str} irrigation={irr}")
            zones_data[f"zone{z}"] = {
                "soil_moisture": round(m, 2) if m is not None else None,
                "temperature":   round(self._temp[z], 2) if self._temp[z] else None,
                "humidity":      round(self._humidity[z], 2) if self._humidity[z] else None,
                "irrigation":    irr
            }
        self.get_logger().info("[IrrigationController] Status:\n" + "\n".join(lines))
        payload = json.dumps({"timestamp": ts, "system": "Smart Farm Digital Twin", "zones": zones_data}, indent=2)
        self._pub_status.publish(String(data=payload))

def main(args=None):
    rclpy.init(args=args)
    node = IrrigationControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
