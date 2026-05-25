#!/bin/bash
set -e

echo "======================================================="
echo "   Smart Farm Digital Twin - WSL2 Installer"
echo "======================================================="

OS_ID=$(. /etc/os-release && echo "$ID$VERSION_ID")
if [[ "$OS_ID" != "ubuntu24.04" ]]; then
    echo "[!] Expected Ubuntu 24.04. Current OS:"
    cat /etc/os-release | grep PRETTY_NAME
    echo "[!] Continuing anyway - some steps may fail."
fi

RAM_GB=$(awk '/MemTotal/{printf "%d", $2/1024/1024}' /proc/meminfo)
echo "[...] Detected RAM: ${RAM_GB} GB"

echo "[...] Step 1 - Setting locale"
sudo apt-get install -y locales > /dev/null
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
echo "[ok] Locale configured"

echo "[...] Step 2 - Adding ROS 2 Jazzy repository"
if ! grep -q "ros2" /etc/apt/sources.list.d/*.list 2>/dev/null; then
    sudo apt-get install -y software-properties-common curl > /dev/null
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
        | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt-get update > /dev/null
fi
echo "[ok] ROS 2 repository ready"

echo "[...] Step 3 - Installing ROS 2 Jazzy base"
sudo apt-get install -y ros-jazzy-ros-base ros-jazzy-ros-gz python3-colcon-common-extensions \
    python3-rosdep ros-jazzy-robot-state-publisher ros-jazzy-xacro > /dev/null
echo "[ok] ROS 2 Jazzy installed"

echo "[...] Step 4 - Installing rosbridge"
sudo apt-get install -y ros-jazzy-rosbridge-suite > /dev/null
echo "[ok] rosbridge installed"

echo "[...] Step 5 - Installing Python packages"
pip install flask flask-socketio --break-system-packages > /dev/null
echo "[ok] Python packages installed"

echo "[...] Step 6 - Installing Gazebo Harmonic"
if ! command -v gz &> /dev/null; then
    sudo apt-get install -y gz-harmonic > /dev/null
fi
echo "[ok] Gazebo Harmonic installed"

echo "[...] Step 7 - Initialising rosdep"
sudo rosdep init 2>/dev/null || true
rosdep update 2>/dev/null

echo "[...] Step 8 - Building workspace"
cd "$(dirname "$0")/.."
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install --parallel-workers 2 --executor sequential
echo "[ok] Workspace built"

echo "[...] Step 9 - Adding source to bashrc"
SETUP_LINE="source $(pwd)/install/setup.bash"
grep -qxF "$SETUP_LINE" ~/.bashrc || echo "$SETUP_LINE" >> ~/.bashrc

echo ""
echo "======================================================="
echo "   Installation complete!"
echo "   Run: source ~/.bashrc"
echo "   Then: ./scripts/run.sh"
echo "======================================================="
