#!/usr/bin/env python3
"""
smart_farm_dashboard.py
Smart Farm Digital Twin - Web Dashboard

A Flask + SocketIO web dashboard that subscribes to all farm sensor
and irrigation topics and streams live data to a browser via WebSocket.

Access at: http://localhost:5000

Author: Shah Md Abul Hasan, University of Georgia
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

state = {
    "zone1": {"moisture": 0, "temp": 0, "humidity": 0, "irrigation": "OFF"},
    "zone2": {"moisture": 0, "temp": 0, "humidity": 0, "irrigation": "OFF"},
    "zone3": {"moisture": 0, "temp": 0, "humidity": 0, "irrigation": "OFF"},
}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Smart Farm Digital Twin</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e0e0e0}
header{background:#1a1d2e;padding:16px 24px;border-bottom:1px solid #2a2d3e;display:flex;align-items:center;gap:12px}
header h1{font-size:20px;font-weight:600;color:#fff}
.badge{background:#00c896;color:#000;font-size:11px;font-weight:600;padding:3px 8px;border-radius:12px}
.dot{width:8px;height:8px;background:#00c896;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
.container{padding:24px;max-width:1200px;margin:0 auto}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.scard{background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:16px}
.scard .label{font-size:12px;color:#888;margin-bottom:8px}
.scard .value{font-size:28px;font-weight:700;color:#fff}
.scard .sub{font-size:12px;color:#555;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px;margin-bottom:24px}
.card{background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:20px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.card-title{font-size:15px;font-weight:600;color:#fff}
.irr{font-size:12px;font-weight:600;padding:4px 10px;border-radius:8px}
.irr-on{background:#1a3a2a;color:#00c896;border:1px solid #00c896}
.irr-off{background:#2a1a1a;color:#888;border:1px solid #444}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.metric{background:#0f1117;border-radius:8px;padding:12px;text-align:center}
.metric .ml{font-size:11px;color:#888;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}
.metric .mv{font-size:22px;font-weight:700}
.bar{height:8px;background:#2a2d3e;border-radius:4px;overflow:hidden;margin-bottom:8px}
.fill{height:100%;border-radius:4px;transition:width .8s ease}
.bar-label{font-size:12px;color:#888;display:flex;justify-content:space-between}
.chart-card{background:#1a1d2e;border:1px solid #2a2d3e;border-radius:12px;padding:20px;margin-bottom:24px}
.chart-title{font-size:15px;font-weight:600;color:#fff;margin-bottom:16px}
footer{text-align:center;padding:16px;color:#444;font-size:12px;border-top:1px solid #2a2d3e}
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <h1>Smart Farm Digital Twin</h1>
  <span class="badge">LIVE</span>
</header>
<div class="container">
  <div class="summary">
    <div class="scard"><div class="label">Active irrigation zones</div><div class="value" id="active">0</div><div class="sub">out of 3 zones</div></div>
    <div class="scard"><div class="label">Average soil moisture</div><div class="value" id="avg-m">--%</div><div class="sub">across all zones</div></div>
    <div class="scard"><div class="label">Average temperature</div><div class="value" id="avg-t">--C</div><div class="sub">field average</div></div>
    <div class="scard"><div class="label">System status</div><div class="value" style="color:#00c896;font-size:20px">Online</div><div class="sub">ROS 2 Jazzy connected</div></div>
  </div>
  <div class="grid">
    {% for n in [1,2,3] %}
    <div class="card">
      <div class="card-header"><span class="card-title">Zone {{ n }}</span><span class="irr irr-off" id="z{{ n }}-irr">OFF</span></div>
      <div class="metrics">
        <div class="metric"><div class="ml">Moisture</div><div class="mv" id="z{{ n }}-m" style="color:#4fc3f7">--%</div></div>
        <div class="metric"><div class="ml">Temp</div><div class="mv" id="z{{ n }}-t" style="color:#ffb74d">--C</div></div>
        <div class="metric"><div class="ml">Humidity</div><div class="mv" id="z{{ n }}-h" style="color:#81c784">--%</div></div>
      </div>
      <div class="bar"><div class="fill" id="z{{ n }}-bar" style="width:0%;background:#4fc3f7"></div></div>
      <div class="bar-label"><span>0%</span><span>Soil moisture</span><span>100%</span></div>
    </div>
    {% endfor %}
  </div>
  <div class="chart-card">
    <div class="chart-title">Soil moisture history (last 30 readings)</div>
    <canvas id="chart" height="100"></canvas>
  </div>
</div>
<footer>Smart Farm Digital Twin &mdash; ROS 2 Jazzy + Gazebo Harmonic &mdash; Shah Md Abul Hasan, University of Georgia</footer>
<script>
const socket=io();
const ctx=document.getElementById('chart').getContext('2d');
const labels=[],d1=[],d2=[],d3=[];
const chart=new Chart(ctx,{type:'line',data:{labels,datasets:[
  {label:'Zone 1',data:d1,borderColor:'#4fc3f7',backgroundColor:'rgba(79,195,247,0.1)',tension:0.4,fill:true,pointRadius:2},
  {label:'Zone 2',data:d2,borderColor:'#f48fb1',backgroundColor:'rgba(244,143,177,0.1)',tension:0.4,fill:true,pointRadius:2},
  {label:'Zone 3',data:d3,borderColor:'#81c784',backgroundColor:'rgba(129,199,132,0.1)',tension:0.4,fill:true,pointRadius:2}
]},options:{responsive:true,animation:{duration:300},
  scales:{x:{ticks:{color:'#555',maxTicksLimit:10},grid:{color:'#1e2130'}},
          y:{ticks:{color:'#555'},grid:{color:'#1e2130'},min:0,max:100}},
  plugins:{legend:{labels:{color:'#888',boxWidth:12}}}}});
function col(v){return v<20?'#ef5350':v<30?'#ffa726':v>70?'#ab47bc':'#4fc3f7'}
socket.on('update',data=>{
  const z=data.zones;let active=0,totM=0,totT=0;
  [['zone1',1],['zone2',2],['zone3',3]].forEach(([key,n])=>{
    const zd=z[key],m=zd.moisture.toFixed(1),t=zd.temp.toFixed(1),h=zd.humidity.toFixed(1),irr=zd.irrigation,c=col(zd.moisture);
    document.getElementById(`z${n}-m`).textContent=m+'%';
    document.getElementById(`z${n}-m`).style.color=c;
    document.getElementById(`z${n}-t`).textContent=t+'C';
    document.getElementById(`z${n}-h`).textContent=h+'%';
    document.getElementById(`z${n}-bar`).style.width=Math.min(zd.moisture,100)+'%';
    document.getElementById(`z${n}-bar`).style.background=c;
    const b=document.getElementById(`z${n}-irr`);b.textContent=irr;b.className='irr '+(irr==='ON'?'irr-on':'irr-off');
    if(irr==='ON')active++;totM+=zd.moisture;totT+=zd.temp;
  });
  document.getElementById('active').textContent=active;
  document.getElementById('avg-m').textContent=(totM/3).toFixed(1)+'%';
  document.getElementById('avg-t').textContent=(totT/3).toFixed(1)+'C';
  const now=new Date().toLocaleTimeString();
  labels.push(now);d1.push(z.zone1.moisture);d2.push(z.zone2.moisture);d3.push(z.zone3.moisture);
  if(labels.length>30){labels.shift();d1.shift();d2.shift();d3.shift();}
  chart.update();
});
</script>
</body>
</html>
"""

QOS = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT,
                 history=QoSHistoryPolicy.KEEP_LAST, depth=5)


class DashboardNode(Node):
    def __init__(self):
        super().__init__('dashboard_node')
        for z in [1, 2, 3]:
            self.create_subscription(Float32, f'/farm/zone{z}/soil_moisture',
                lambda m, z=z: self._cb(m, 'moisture', z), QOS)
            self.create_subscription(Float32, f'/farm/zone{z}/temperature',
                lambda m, z=z: self._cb(m, 'temp', z), QOS)
            self.create_subscription(Float32, f'/farm/zone{z}/humidity',
                lambda m, z=z: self._cb(m, 'humidity', z), QOS)
            self.create_subscription(String, f'/farm/zone{z}/irrigation_cmd',
                lambda m, z=z: self._cb_irr(m, z), QOS)
        self.create_timer(1.0, self._push)

    def _cb(self, msg, field, zone):
        state[f'zone{zone}'][field] = round(msg.data, 2)

    def _cb_irr(self, msg, zone):
        state[f'zone{zone}']['irrigation'] = msg.data.strip()

    def _push(self):
        socketio.emit('update', {'zones': state})


@app.route('/')
def index():
    return render_template_string(HTML)


def ros_thread():
    rclpy.init()
    rclpy.spin(DashboardNode())


if __name__ == '__main__':
    threading.Thread(target=ros_thread, daemon=True).start()
    print("\n" + "=" * 50)
    print("  Smart Farm Dashboard")
    print("  Open: http://localhost:5000")
    print("=" * 50 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
