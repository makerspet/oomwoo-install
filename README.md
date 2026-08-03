<div align="center">

# OOMWOO Install

*Open-source robot vacuum you build yourself.*

Raspberry Pi · ROS 2 · Docker · Ubuntu · Dev environment

![License](https://img.shields.io/badge/license-Apache--2.0-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
[![Part of OOMWOO](https://img.shields.io/badge/part%20of-OOMWOO-5eead4)](https://github.com/makerspet/oomwoo)

</div>

Raspberry Pi software + development software for [OOMWOO](https://github.com/makerspet/oomwoo)
open-source robot vacuum.

![oomwoo Open source vacuum cleaner placeholder illustration](https://github.com/makerspet/oomwoo/raw/main/assets/vacuum-no-dock-front.webp)

## Deploy on Raspberry Pi

On your Raspberry Pi 4/5 2GB+ run

```
git clone https://github.com/makerspet/oomwoo-install
source oomwoo-install/ubuntu/install_oomwoo_runtime_jazzy.sh
```

Measure the onboard runtime before changing the minimum Pi/CM memory profile:

```bash
oomwoo-runtime-benchmark record --help
oomwoo-runtime-benchmark compare --help
```

The [Pi runtime benchmark guide](docs/pi_runtime_benchmark.md) covers repeatable
idle, 5 Hz SLAM, and Nav2 runs, ROS 2 composition comparisons, and the measured
decision gate for a lower-cost 2 GB target.

## Develop OOMWOO software - no hardware needed

The quickest way to try OOMWOO is the ROS 2 development environment in Docker — no
robot, GPU, or display required:

```
docker pull makerspet/oomwoo:jazzy-dev
docker run -d --name oomwoo makerspet/oomwoo:jazzy-dev sleep infinity
docker exec -it oomwoo bash
```

## Tutorials
- Simulate vacuum in Gazebo: [Simulate OOMWOO-One](https://makerspet.com/blog/simulate-oomwoo-one-robot-vacuum-in-gazebo-with-ros-2/) in Gazebo with ROS 2 (no hardware needed)
- Write a [Hello-World](https://makerspet.com/blog/write-your-first-oomwoo-ros-2-package/) software package
- Install, operate a real (temp placeholder) vacuum cleaner
[Part 1](https://makerspet.com/blog/tutorial-connect-robot-vacuum-cleaner-to-ros-2-proscenic-m6-pro/) and [Part 2](https://makerspet.com/blog/tutorial-part-2-drive-map-navigate-your-proscenic-m6-pro-in-ros-2/).
- [Simulate](https://makerspet.com/blog/simulate-the-proscenic-m6-pro-robot-vacuum-in-gazebo-with-ros-2/) temp vacuum cleaner 
- Run coverage cleaning (agent quickstart): [Headless sim & coverage cleaning](https://makerspet.com/blog/oomwoo-headless-sim-coverage-cleaning-llm-agents/) for LLM agents
- All tutorials: [makerspet.com/learn](https://makerspet.com/learn/)
- Questions & help: [Discord](https://discord.gg/3y2JKz5T25)

## Commands reference

Run these inside the dev container (`docker exec -it oomwoo bash`). The default robot
model is `oomwoo_one`; switch it with `kaia config robot.model <package>` or a
`robot_model:=<package>` launch argument.

**Simulate in Gazebo**
```
ros2 launch oomwoo_gazebo world.launch.py                 # with the Gazebo GUI (needs a display)
ros2 launch oomwoo_gazebo world.launch.py headless:=true  # headless (Docker / CI, no display)
```

**Drive the robot**
```
ros2 run kaiaai_teleop teleop_keyboard                                       # keyboard teleop
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}'   # or publish velocity
```

**Map & navigate (SLAM)** — with a world running, in another terminal
```
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true slam:=True             # build a map
ros2 run nav2_map_server map_saver_cli -f ~/maps/map                                      # save the map
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true map:=~/maps/map.yaml   # navigate a saved map
ros2 launch oomwoo_bringup monitor_robot.launch.py use_sim_time:=true                     # RViz view
```

**Coverage cleaning (headless)**
```
ros2 launch oomwoo_sim_support coverage_regression.launch.py   # sim + Nav2 + coverage planner + meter
ros2 topic echo /coverage_meter/ratio                          # coverage fraction, 0.0 -> 1.0
```
See the [headless sim & coverage cleaning](https://makerspet.com/blog/oomwoo-headless-sim-coverage-cleaning-llm-agents/) quickstart for the agent/CI workflow.

**Inspect sensors**
```
ros2 topic echo /scan                                                 # 2D LiDAR
ros2 topic echo /bumper_left/contact ros_gz_interfaces/msg/Contacts   # front bumpers
```

**Physical robot (placeholder Proscenic M6 Pro)** — see the [connect](https://makerspet.com/blog/tutorial-connect-robot-vacuum-cleaner-to-ros-2-proscenic-m6-pro/) and [drive, map &amp; navigate](https://makerspet.com/blog/tutorial-part-2-drive-map-navigate-your-proscenic-m6-pro-in-ros-2/) tutorials
```
kaia config robot.model proscenic_m6pro
ros2 launch proscenic_m6pro bringup.launch.py robot_ip:=<robot-ip>
ros2 launch oomwoo_bringup navigation.launch.py slam:=True
```

## Release history

### 7/24/2026
- Rviz shows cleaning plan
  - `ros2 launch oomwoo_bringup monitor_robot.launch.py`
  - add `/coverage_planner/plan`, Fixed Frame = map
- reactive navigation for cleaning
  - experimental, replaces Nav2 for cleaning tasks

```
ros2 launch oomwoo_sim_support coverage_regression.launch.py gui:=true \
  world:=$(ros2 pkg prefix oomwoo_gazebo)/share/oomwoo_gazebo/worlds/living_room.world \
  map:=$(ros2 pkg prefix oomwoo_sim_support)/share/oomwoo_sim_support/maps/living_room.yaml \
  x_pose:=0.32 y_pose:=1.59 executor:=reactive

```

### 7/21/2026
- clean using an existing map; Boustrophedon, clunky, slow, fails often
  - packages in makerspet/oomwoo-ros2-tools
- added bumpers, verified working
- added localization (kidnapped robot); not tested
- forked kaiaai_gazebo, kaiaai_bringup to oomwoo_gazebo, oomwoo_bringup

### 7/8/2026
- added a first Raspberry Pi 4/5 4GB runtime install plan
- added simulated CPU-MCU serial I/O placeholder

### 7/1/2026
- added oomwoo-one ROS2 robot description package (simulation only)

### 6/26/2026
- added https://github.com/remakeai/vacuum_ros2_bridge
  - LiDAR compute moved to vacuum_ros2_bridge

### 6/18/2026
- added bumper sensors for proscenic-m6pro
- fixed Gazebo living world marble table collision mesh

### 6/16/2026
- added Proscenic M6 Pro [robot description](https://github.com/makerspet/proscenic-m6pro)
  - `kaia config robot.model proscenic_m6pro`
