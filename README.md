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

## Develop on Linux/Windows WSL2 - no hardware needed

The quickest way to try OOMWOO is the ROS 2 development environment in Docker — no
robot, GPU, or display required:

```
docker pull makerspet/oomwoo:jazzy-dev
docker run -d --name oomwoo makerspet/oomwoo:jazzy-dev sleep infinity
docker exec -it oomwoo bash
```

## Develop on Mac

See [Mac pixi instructions](https://github.com/makerspet/oomwoo/tree/main/contributions/mac-dev-env/DingoOz).

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

### 8/11/2026

- one RViz window for wall-segment estimation: `navigation.launch.py` now takes an `rviz_config` argument (just like `monitor_robot.launch.py`), and `bump_map.rviz` folds in the Nav2 displays (global/local costmaps, plans, AMCL particle swarm, Nav2 goal tool) on top of the bump-map layers
  - launch navigation straight into the bump map — no second RViz window from `monitor_robot.launch.py`
- `wall_clean_bump_out.launch.py` now *starts `bump_map.launch.py` for you* (pass `bump_map:=false` to skip) — one fewer terminal to build the tactile keep-out map while cleaning
- `bump_map.rviz` decluttered for wall-segment estimation: the semi-transparent `/bump_map` keep-out overlay and the Global Planner / Controller costmap groups are now *off by default* (the red bump-wall segments stay on), and the top-down view is rotated to match the Gazebo default orientation; the Selection / Tool Properties / Views panes are hidden and the `/odom` heading arrow is shown so you can see which way the vacuum faces
- wall cleaning cruise arc is now tuned by *radius* instead of angular rate: the `arc_omega` parameter is replaced by `arc_radius` (metres, default 1.5), and the turn rate is derived as `v_cruise / arc_radius` — so the arc shape stays the same at any cruise speed. Retune with `kaia set clean.arc_radius 1.0` (smaller = tighter into the wall). If you had set `clean.arc_omega`, switch it to `clean.arc_radius`
- `bump_map` now builds its tactile map in the **`map` frame**: it starts in `odom`, then promotes to `map` the instant localization comes up and rebases the contacts captured so far — so the wall segments stay nailed to the map instead of drifting with the LiDAR scan when AMCL wobbles (the pure-bumper, no-localization mode stays in `odom`)

```
ros2 launch oomwoo_gazebo world.launch.py
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true \
  map:=/ros_ws/src/oomwoo_gazebo/map/living_room.yaml rviz_config:=bump_map.rviz
ros2 launch oomwoo_clean wall_clean_bump_out.launch.py use_sim_time:=true  # also starts bump_map
```

### 8/11/2026

- the Gazebo sim now starts with the stereo *cameras off by default* (heaviest sensor, unused for now) — faster out of the box; turn them on with `enable_cameras:=true`
- `navigation.launch.py` can *auto-localize*: it seeds AMCL at the known start pose so the `map` frame is available without the manual RViz "2D Pose Estimate" (sim only by default). This unblocks bump-map wall-segment estimation, which needs the map frame
  - auto-localize runs in simulations, when `use_sim_time:=true`
  - force disable `auto_localize:=false`
- added `bump_map.rviz` to visualize the bump map over the SLAM map

```
ros2 launch oomwoo_gazebo world.launch.py
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true \
  map:=/ros_ws/src/oomwoo_gazebo/map/living_room.yaml           # auto-localizes now
ros2 launch oomwoo_clean bump_map.launch.py use_sim_time:=true
ros2 launch oomwoo_bringup monitor_robot.launch.py use_sim_time:=true rviz_config:=bump_map.rviz
```

### 8/10/2026

- added per-sensor on/off switches to speed up the Gazebo simulation
  - the rendering sensors (cameras and the front ToF most of all, then the side ranges and LiDAR) slow the sim down; turn the ones you don't need off at launch
  - the sensor frames stay in the model; only the gz sensor (the render cost) is dropped

```
ros2 launch oomwoo_gazebo world.launch.py enable_cameras:=false enable_tof:=false   # faster
ros2 launch oomwoo_gazebo world.launch.py \
  enable_ranges:=false enable_tof:=false enable_cameras:=false enable_imu:=false     # nav only (LiDAR)
```

### 8/10/2026

- added an RViz config to eyeball all the sim sensors at once (LiDAR, side ranges, front ToF cloud, both cameras, bump map)
  - except IMU
  - `monitor_robot.launch.py` now takes an `rviz_config` argument to pick any `.rviz` file from the robot package `rviz/` folder

```
ros2 launch oomwoo_gazebo world.launch.py
ros2 launch oomwoo_bringup monitor_robot.launch.py use_sim_time:=true rviz_config:=sensors.rviz
```

### 8/10/2026

- added a tactile "bump map" — the truly-solid keep-out layer, built from the bumpers alone
  - LiDAR/cameras see couch skirts, bed valances and curtains as solid, but a vacuum should clean under/through them; only a physical bump proves something is *truly* solid, so a coverage planner can still clean the rest
  - the `bump_map` node turns bumper contacts into `/bump_map` (OccupancyGrid keep-out layer) + `/bump_map/walls` (RViz wall segments) + `/bump_event` (new `oomwoo_msgs/BumpEvent`: contact point, approach, which bumper side)
  - contacts are placed along the robot's approach heading and accumulated; the map is in `map` when localized, else `odom`

```
ros2 launch oomwoo_gazebo world.launch.py
# localize (map->odom)
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true map:=/ros_ws/src/oomwoo_gazebo/map/living_room.yaml
ros2 launch oomwoo_clean bump_map.launch.py use_sim_time:=true
ros2 run kaiaai_teleop teleop_keyboard
# point the vacuum at a wall, then bump-out clean to build the map
ros2 launch oomwoo_clean wall_clean_bump_out.launch.py use_sim_time:=true
# RViz: add a Map on /bump_map and a MarkerArray on /bump_map/walls
```

### 8/10/2026

- added more sensors to oomwoo-one URDF (Gazebo simulation)
  - front multizone ToF depth sensor (16x8 zones, 120° FoV, models two VL53L7CX) → `/tof_front/points`
  - front stereo cameras (VGA, 120° FoV, OV5647-equivalent) → `/camera_left/image`, `/camera_right/image`
  - IMU: gyro + accelerometer + orientation → `/imu`
- added a simulation odometry source switch: ground-truth model pose (default) or wheel-encoder odometry
  - the selected source drives `/odom` + `/tf`; the other is always published on `/odom_truth` / `/odom_wheel` so wheel slip can be measured later
- documented oomwoo-one simulation sensors, topics, URDF parameters and world launch arguments in its [README](https://github.com/makerspet/oomwoo-one/blob/jazzy/README.md#simulation-sensors-topics--tuning)
- gave the reactive bump-out cleaner its own `wall_clean_bump_out.launch.py`, freeing `wall_clean.launch.py` for the upcoming full wall following

```
ros2 launch oomwoo_gazebo world.launch.py                     # ground-truth odom (default)
ros2 launch oomwoo_gazebo world.launch.py odom_source:=wheel  # wheel-encoder odom, slip drifts
ros2 topic echo /imu
ros2 topic hz /tof_front/points
ros2 run rqt_image_view rqt_image_view                        # view /camera_left/image
```

### 8/9/2026

- wall-follow-bump-out now backs vacuum "out" the way the vacuum drove "in" - as opposed to backing "up" straight
  - back-out retracing its path makes vacuum less likely to wedge somewhere new
  - documentation https://github.com/makerspet/oomwoo-ros2-tools/blob/jazzy/docs/wall-follow-bump-out.md

### 8/9/2026

- fixed non-interactive bash to have same context as interactive
  - that caused OpenGL go missing, broke LiDAR scans in headless Gazebo simulations
- added side distance sensors to oomwoo-one URDF
- kaia CLI sets ROS2 parameters, [documentation](https://github.com/kaiaai/kaiaai/blob/jazzy/docs/cli.md)

```
ros2 topic echo /range_right
ros2 topic echo /range_left
```

### 8/8/2026
- added rudimentary reactive cleaning along the wall by "bumping out" the wall
  - works, LiDAR is not used
  - "bumping out" is needed when furniture has covers that appear solid in LiDAR scans, but the vacuum can still get under the furniture cover (e.g. to clean under the sofa)
- fixed oomwoo-one URDF bumper height to match the vacuum cylinder body height
- upgraded kaia CLI to manage configuration variables

```
ros2 launch oomwoo_gazebo world.launch.py
ros2 launch oomwoo_bringup monitor_robot.launch.py
ros2 run kaiaai_teleop teleop_keyboard
# Point the vacuum at the wall to be cleaned
ros2 launch oomwoo_clean wall_clean.launch.py use_sim_time:=true
# Optional - wall clean bump-out settings
# kaia set clean.arc_omega 0.1
# kaia set clean.turn_right_deg 10
# turn_right_deg / turn_left_deg / turn_both_deg 20/90/60
```

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
