#!/bin/bash
# Install Kaia.ai ROS2 platform https://github.com/kaiaai/install
. /opt/ros/jazzy/setup.bash
mkdir ~/uros_ws && cd ~/uros_ws
git clone --depth 1 -b jazzy https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
sudo apt update
sudo apt install -y ed python3-pip
sudo apt install -y ros-jazzy-rmw-fastrtps-cpp
sudo apt remove -y ros-jazzy-rmw-cyclonedds-cpp
sudo rosdep init
rosdep update --rosdistro jazzy
rosdep install --from-paths src --ignore-src -y
colcon build
. install/local_setup.sh
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
rm -rf log/ build/ src/

cd ~/.ros
wget https://raw.githubusercontent.com/kaiaai/install/main/ubuntu/etc/disable_fastdds_shm.xml
wget https://raw.githubusercontent.com/kaiaai/install/main/ubuntu/etc/disable_fastdds_shm_localhost_only.xml
cd ~

export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export MICROROS_DISABLE_SHM=1

mkdir ~/ros_ws && cd ~/ros_ws
sudo apt install -y python3-pip nano inotify-tools ros-jazzy-joint-state-publisher-gui ros-jazzy-cartographer-ros ros-jazzy-nav2-map-server ros-jazzy-nav2-bringup
# https://www.youtube.com/watch?v=b8VwSsbZYn0
sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-ros-gz
sudo apt install ros-jazzy-gz-ros2-control
sudo apt install ros-jazzy-joy*

# TODO fix
pip3 install aiortc aiohttp opencv-python
sudo apt autoremove -y
# sudo rm -rf /var/lib/apt/lists/*

git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_msgs src/kaiaai_msgs
git clone -b dev --depth 1 https://github.com/kaiaai/kaiaai src/kaiaai
git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_telemetry src/kaiaai_telemetry
git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_teleop src/kaiaai_teleop
git clone -b dev --depth 1 https://github.com/kaiaai/kaiaai_bringup src/kaiaai_bringup
git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_fido src/makerspet_fido
git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_loki src/makerspet_loki
git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_snoopy src/makerspet_snoopy
git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_mini src/makerspet_mini
git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet src/makerspet
git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_gazebo src/kaiaai_gazebo
git clone --depth 1 https://github.com/kaiaai/m-explore-ros2 src/m-explore-ros2
git clone --depth 1 https://github.com/kaiaai/auto_mapper src/auto_mapper
git clone --depth 1 https://github.com/kaiaai/nav2_wfe src/nav2_wfe
colcon build --symlink-install
rm -rf log/
mkdir ~/maps

cat <<EOF >> ~/.bashrc
. ~/uros_ws/install/setup.bash
. ~/ros_ws/install/setup.bash
alias kaia='ros2 run kaiaai cli'

export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export MICROROS_DISABLE_SHM=1

if [ "$MICROROS_DISABLE_SHM" = "1" ] ; then
    if [ "$ROS_LOCALHOST_ONLY" = "1" ] ; then
        export FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/disable_fastdds_shm_localhost_only.xml
    else
        export FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/disable_fastdds_shm.xml
    fi
fi
echo "\033[31mVisit https://github.com/kaiaai/kaiaai for help\033[0m"
EOF

cat <<EOF >> ~/.bash_history
exit
ros2 launch kaiaai_bringup navigation.launch.py use_sim_time:=true slam:=True
ros2 launch kaiaai_gazebo world.launch.py
ros2 param set /pet lidar.scan.freq.target 7.0
ros2 run nav2_map_server map_saver_cli -f ~/maps/map --ros-args -p save_map_timeout:=60.0
ros2 launch kaiaai_bringup navigation.launch.py slam:=True
ros2 launch kaiaai_bringup monitor_robot.launch.py
ros2 run kaiaai_teleop teleop_keyboard
ros2 launch kaiaai_bringup physical.launch.py
EOF
