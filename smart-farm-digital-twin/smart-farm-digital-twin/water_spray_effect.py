#!/usr/bin/env python3
"""
water_spray_effect.py
Smart Farm Digital Twin - Water Spray Visual Effect

Listens to irrigation command topics and spawns/removes blue sphere
droplets in Gazebo Harmonic to simulate water spray from sprinklers
when irrigation is active.

Author: Shah Md Abul Hasan, University of Georgia
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import subprocess, threading, time, math

SPRINKLER_POSITIONS = {
    1: (-5.0, 5.0, 1.0),
    2: ( 0.0, 2.0, 1.0),
    3: ( 5.0,-1.0, 1.0),
}

QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=5
)

WORLD = "virtual_maize_field"


def spawn_droplet(name, x, y, z):
    sdf = (
        f'<sdf version="1.8"><model name="{name}"><static>true</static>'
        f'<link name="link"><visual name="v"><geometry><sphere><radius>0.06</radius></sphere></geometry>'
        f'<material><ambient>0.2 0.5 1 1</ambient><diffuse>0.2 0.5 1 1</diffuse></material>'
        f'</visual></link><pose>{x} {y} {z} 0 0 0</pose></model></sdf>'
    )
    path = f"/tmp/{name}.sdf"
    open(path, "w").write(sdf)
    subprocess.run([
        "gz", "service", "-s", f"/world/{WORLD}/create",
        "--reqtype", "gz.msgs.EntityFactory",
        "--reptype", "gz.msgs.Boolean",
        "--timeout", "3000",
        "--req", f'sdf_filename: "{path}"'
    ], capture_output=True)


def delete_model(name):
    subprocess.run([
        "gz", "service", "-s", f"/world/{WORLD}/remove",
        "--reqtype", "gz.msgs.Entity",
        "--reptype", "gz.msgs.Boolean",
        "--timeout", "3000",
        "--req", f'name: "{name}" type: 2'
    ], capture_output=True)


class SprayEffect:
    def __init__(self, zone, x, y, z):
        self.zone = zone
        self.x, self.y, self.z = x, y, z
        self.active = False
        self.droplets = []

    def start(self):
        if self.active:
            return
        self.active = True
        threading.Thread(target=self._animate, daemon=True).start()
        print(f"[Spray] Zone {self.zone} ON")

    def stop(self):
        self.active = False
        time.sleep(0.3)
        for n in self.droplets:
            delete_model(n)
        self.droplets.clear()
        print(f"[Spray] Zone {self.zone} OFF")

    def _animate(self):
        count = 0
        while self.active:
            for i in range(6):
                if not self.active:
                    break
                angle = (i / 6) * 2 * math.pi + count * 0.4
                r = 0.2 + (count % 4) * 0.15
                name = f"sp_z{self.zone}_{count}_{i}"
                spawn_droplet(
                    name,
                    self.x + r * math.cos(angle),
                    self.y + r * math.sin(angle),
                    self.z - (count % 4) * 0.12
                )
                self.droplets.append(name)
            if len(self.droplets) > 24:
                for n in self.droplets[:12]:
                    delete_model(n)
                self.droplets = self.droplets[12:]
            count += 1
            time.sleep(0.7)


class WaterSprayNode(Node):
    def __init__(self):
        super().__init__('water_spray_node')
        self.effects = {z: SprayEffect(z, *pos) for z, pos in SPRINKLER_POSITIONS.items()}
        for z in [1, 2, 3]:
            self.create_subscription(
                String, f'/farm/zone{z}/irrigation_cmd',
                lambda msg, z=z: self._on_irr(msg, z), QOS
            )
        self.get_logger().info("Water spray node ready")

    def _on_irr(self, msg, zone):
        if msg.data.strip() == "ON":
            self.effects[zone].start()
        else:
            threading.Thread(target=self.effects[zone].stop, daemon=True).start()


def main():
    rclpy.init()
    rclpy.spin(WaterSprayNode())


if __name__ == '__main__':
    main()
