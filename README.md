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

### 8/27/2026

- **Large-obstacle localization stress test** — new `scan_obstacle_injector` (`oomwoo_sim_support`) paints a big off-map obstacle into a contiguous arc of `/scan` → `/scan_stress` (deterministic, sweep-capable), so a scan-matcher faces a large *coherent* occlusion rather than scattered noise. `localization_stress.launch.py` localizes slam_toolbox on the stressed scan and scores `loc_err_slam` against ground truth; `filter:=true` instead routes slam through `localization_health`'s `/scan_filtered`, to A/B whether stripping the obstacle recovers the pose. slam_toolbox publishes `/map` here, so no nav2/AMCL/map_server is needed

```
# terminal 1 — sim (robot_wheels = wheel odom, /odom_truth is ground truth)
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
# terminal 2 — BASELINE: slam matches the raw stressed scan
ros2 launch oomwoo_sim_support localization_stress.launch.py use_sim_time:=true map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
# then FILTERED: slam matches /scan_filtered (obstacle stripped) — compare loc_err_slam
ros2 launch oomwoo_sim_support localization_stress.launch.py use_sim_time:=true map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml filter:=true
ros2 run foxglove_bridge foxglove_bridge  # plot /loc_err_slam/pos_err_m and /loc_err_slam/yaw_err_deg
# widen/sweep to find where it bites:  obstacle_width_deg:=90 obstacle_sweep:=true
```

### 8/26/2026

- **Sharper scan tracking through fast turns** — slam_toolbox was re-matching at only ~2 Hz (`minimum_time_interval: 0.5`), so a fast-spinning robot dead-reckoned ~0.5 s of odometry between matches and the scan cloud visibly lagged then snapped in RViz. Tightened to `0.1` (under the 5 Hz scan period) and zeroed `minimum_travel_distance`/`minimum_travel_heading`, so it re-matches on essentially every scan and stays registered through aggressive spins
- **Tracked the residual "stop flick" to wheel slip** — the one-frame angular jump left after the tuning is *wheel slip*, not a localizer bug: on a hard stop from a fast spin the velocity-controlled wheels halt while the body coasts on inertia, so wheel odometry undershoots the true rotation for a frame (and symmetrically over-reads on spin-up). Each aggressive spin-stop leaves a few degrees of net over-read, which is what accumulates into raw wheel-odom heading drift — the drift slam quietly corrects against the map every scan. It's real physics (a real vacuum slips too), only exercised far harder than a vacuum ever would
- new **`odom_slip`** diagnostic (`oomwoo_sim_support`) — pairs `/odom` (wheel) and `/odom_truth` by header stamp and publishes the slip for Foxglove: `~/slip_rate_dps` (≈ ω_wheel − ω_truth, ~0 while rolling true, spikes + on wheelspin and − on the inertial coast) and de-trended `~/slip_deg`. The raw yaw difference is dominated by a constant frame offset, so the *rate*/accumulation is the real signal
- **hushed** the Ceres `num_threads 50 > 24` glog spam from slam_toolbox (a harmless thread-count cap) via `GLOG_minloglevel`

```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 run oomwoo_sim_support odom_slip --ros-args -p use_sim_time:=true   # slip on ~/slip_rate_dps, ~/slip_deg
ros2 run foxglove_bridge foxglove_bridge  # plot the slip live
ros2 run kaiaai_teleop teleop_keyboard    # spin up, then stop abruptly, and watch ~/slip_rate_dps spike
```

- moved `localization_lost` from localization_health to localization_manager
  - localization_manager handles robot-lost policy (when to flag robot as lost - and what to do when that happens)
  - localization_health handles scan quality compute
- moved `dynamic_obstacles` from localization_health to the perception node
  - the perception node is better suited to decide which obstacles are dynamic

### 8/24/2026

- manually testing `/dynamic_obstacles` detection

```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true auto_recovery:=false map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 run oomwoo_localization localization_health --ros-args -p use_sim_time:=true
ros2 run kaiaai_teleop teleop_keyboard

ros2 topic echo /scan_filtered
ros2 topic echo /localization_health/dynamic_obstacles
ros2 topic echo /localization_health/scan_scored  # walls bright = static, ball dark = dynamic
ros2 topic echo /localization_health/quality
```

### 8/24/2026

- **stress mode** — the relocalizer's confidence gate is now *proven* to refuse when it genuinely can't tell. An adversarial regression feeds the real branch-and-bound matcher scans corrupted on purpose (a dynamic obstacle, a removed wall, a symmetric room) and asserts the product-grade invariant: it accepts a fix **only when that fix is correct**, and on a symmetric room (match score near 1.0, confidence 0.0) it **refuses** rather than commit to a coin-flip. Runs in ~1 s as a CI test
- **scan filtering** (`localization_health`) — dynamic obstacles (a stray box, a rolling ball) are stripped from a republished **`/scan_filtered`** so they stop dragging the running scan match down; the segmented clusters go out on `~/dynamic_obstacles`. It filters only while the pose is trusted, and never blanks more than a set fraction of the scan
- **`~/scan_scored`** — the full scan (nothing dropped) republished with each ray's **static-ness** in its intensity: `exp(-d²/2σ²)`, 1.0 on a mapped wall and → 0 for a dynamic return. A perception/ML node can threshold and cluster it however it likes (experimental API)
- new **`oomwoo_perception`** package with a placeholder `dynamic_object_detector` — a starting point for contributors: it reads `~/scan_scored`, groups the dynamic rays into blobs, and publishes their centroids on `~/objects` (MarkerArray) for RViz. Classification, tracking, and gestures (e.g. tap-a-foot-to-spot-clean) are what you add on top

```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true auto_recovery:=false map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 launch oomwoo_localization localization_recovery.launch.py use_sim_time:=true   # localization_health -> scan_scored + /scan_filtered
ros2 launch oomwoo_perception dynamic_object_detector.launch.py use_sim_time:=true   # dynamic blobs on ~/objects
# push the living-room toy ball in front of the vacuum and watch it flagged in RViz:
#   MarkerArray on /dynamic_object_detector/objects
#   LaserScan on /localization_health/scan_scored (Color Transformer = Intensity)
```

### 8/22/2026

- Cartographer-style [Hess, et al 2016](https://www.semanticscholar.org/paper/Real-time-loop-closure-in-2D-LIDAR-SLAM-Hess-Kohler/579735c1e5b2b0ae7fb42fcb9e2433f3118afd20) global relocalizer works,
```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true auto_recovery:=false map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 launch oomwoo_localization localization_recovery.launch.py use_sim_time:=true
ros2 topic echo /localization_manager/recovery_action
ros2 run foxglove_bridge foxglove_bridge  # Optional, plot localization error
ros2 run kaiaai_teleop teleop_keyboard  # Optional, drive around
ros2 service call /kidnap_injector/kidnap std_srvs/srv/Trigger {}  # Kidnap to random location
ros2 topic pub --once /kidnap_injector/kidnap_to geometry_msgs/msg/PoseStamped "{header: {frame_id: map}, pose: {position: {x: 0.03, y: 1.69}, orientation: {z: -0.939, w: 0.344}}}"  # TV stand
```

- batch/regression test works
  - added hold_s (wait after each relocalization) for visual demo
```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true auto_recovery:=false map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 launch oomwoo_localization reloc_eval.launch.py use_sim_time:=true publish_initialpose:=true csv_path:=/root/maps/reloc_eval.csv hold_s:=3.0
```

### 8/20/2026

- **branch-and-bound global relocalizer** (`oomwoo_localization`): a principled, *guaranteed* answer to "where am I?" instead of AMCL's stochastic global filter. It correlates the current `/scan` against the whole map over all headings (Olson-style correlative matching accelerated with a Cartographer-style max-pool pyramid + branch-and-bound), returning the **exact global optimum** of the search grid — no local-minimum lottery. In sim testing AMCL failed a kidnap ~20% of the time, non-repeatably, confusing one corner for another; the BnB search removes that. It also reports an explicit **confidence margin** (how much the best pose beats the next distinct cluster), so ambiguity (e.g. a symmetric room) is *known and flagged*, not silently guessed — something a particle filter can't do
- new node **`global_relocalizer`**: call the `~/relocalize` service (`oomwoo_localization_msgs/Relocalize`) and get back a pose, score, confidence, and runtime. It is pure mechanism — no motion, no reinit, no "should I trust this" policy (that belongs to an application node); it only reports where the scan says the robot is
- new **`reloc_eval`** batch harness + launch: kidnaps the robot across a systematic pose grid, scores the relocalizer against ground truth, and prints success rate, position/heading error, runtime, and whether the confidence flag actually predicts correctness. Exits non-zero below a threshold, so the same run doubles as a CI regression gate

```
# Evaluate the global relocalizer across a systematic kidnap grid
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true \
  map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 launch oomwoo_localization reloc_eval.launch.py use_sim_time:=true csv_path:=/root/reloc_eval.csv
# or one-shot relocalize by hand:
ros2 service call /global_relocalizer/relocalize oomwoo_localization_msgs/srv/Relocalize {}
```

### 8/19/2026

- new package **`oomwoo_localization`** with a `localization_health` monitor: it scores every `/scan` against the static map at the primary `map→base` pose read from **TF** (continuous — unlike slam_toolbox's sparse `/pose`, whose covariance stays confidently small even on a kidnap). **Quality** = the fraction of beams whose endpoint lands within `match_dist_m` of a mapped wall; a kidnap collapses it (nothing matches) and fires **`/localization_lost`**, while an unmapped shoe/box only dents it. Debug/visibility outputs — `~/quality`, a `~/dist_histogram`, an intensity-labelled `~/scan_annotated` cloud (inlier / outlier / clustered), and a throttled console histogram — let you eyeball which rays matched and the outlier clusters in RViz. Detection only for now; scan filtering and dynamic-obstacle rejection come later
- automatic relocalization now converges reliably: AMCL's `recovery_alpha` (Augmented-MCL random-particle injection) is **off by default** (`recovery:=false`) in `localization_relocalize.launch.py`. Left on, the continuous injection fought the global `/reinitialize_global_localization` and could settle AMCL on the wrong cluster (the far side of the room); pass `recovery:=true` only to exercise passive covariance-based lost-detection
- dev image adds `python3-scipy` (the `localization_health` map distance transform)

```
# Localization health: scan-vs-map match quality + robot-lost detection
ros2 launch oomwoo_localization localization_health.launch.py use_sim_time:=true
# RViz: add a PointCloud2 on /localization_health/scan_annotated, Color Transformer = Intensity
# watch /localization_health/quality collapse on a kidnap; box in front only dents it
```

### 8/18/2026

- `navigation.launch.py` gains a `localization` argument (default **`slam_toolbox`**): navigate a saved map with slam_toolbox scan-matching localization — it loads the map's serialized pose-graph and runs the full Nav2 stack composed in one container, with slam_toolbox owning `map→odom` — or `localization:=amcl` for the particle filter. Falls back to AMCL automatically if the map has no `<map>_serial.posegraph`
- **relocalization + automatic recovery**: `localization_relocalize.launch.py` runs the AMCL-vs-slam_toolbox compare stack + `kidnap_injector` + `relocalize_on_lost`. Teleport ("kidnap") the robot — random via `/kidnap_injector/kidnap`, or to a specified pose via `~/kidnap_to` — and it recovers **automatically**: `relocalize_on_lost` detects the robot is lost (AMCL covariance), calls `/reinitialize_global_localization` and spins in place to re-localize AMCL globally, then re-seeds slam_toolbox (`/initialpose`) at the recovered pose so accurate scan-matching resumes. AMCL does the global "find myself" that scan matching can't, then hands the pose back
- `odom_source` values renamed for clarity: `truth` → **`ground_truth`**, `wheel` → **`robot_wheels`**
- AMCL tuning is now reproducible: `oomwoo_one/config/etc/navigation_tight.yaml` (tuned) and `navigation_loose.yaml` (stock-ish) differ only in the amcl block — pass either as `nav_params:=…` to `localization_compare`
- swapped PlotJuggler for **Foxglove** in the dev image (−~200 MB): `ros2 run foxglove_bridge foxglove_bridge`, then open Foxglove Studio (browser) → `ws://localhost:8765`
- `navigation.launch.py` no longer depends on the sim package `oomwoo_gazebo`: the `map` argument has no default — pass `map:=…` to localize, or `slam:=True` to map
- fixed a sim-clock crash in the `localization_error` meter and `bump_map`: the sliding-window prune subtracted below zero while sim time was still under the window

```
# Navigate a saved map (slam_toolbox localization by default)
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels  # robot_wheels (NOT ground_truth): else the sim odom teleports with the robot
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true \
  map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml rviz_config:=bump_map.rviz  # localization:=amcl switch to AMCL localization

ros2 run foxglove_bridge foxglove_bridge  # Monitor /loc_err_amcl|slam/pos|yaw_err_m/data localization errors
ros2 run kaiaai_teleop teleop_keyboard  # Drive robot a little before kidnap to let AMCL point cloud converge

# Relocalization: kidnap the robot, watch it auto-recover
ros2 launch oomwoo_sim_support localization_relocalize.launch.py use_sim_time:=true \
  map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml  #  recovery:=true auto-detects robot-lost, messes up localization on kidnap
ros2 topic pub --once /kidnap_injector/kidnap_to geometry_msgs/msg/PoseStamped \  # kidnap to a given position -> robot auto-recovers
  "{header: {frame_id: map}, pose: {position: {x: 0.03, y: 1.69}, orientation: {z: -0.939, w: 0.344}}}"
# ros2 service call /kidnap_injector/kidnap std_srvs/srv/Trigger {}   # kidnap to a random position -> robot auto-recovers
```

### 8/16/2026

- Gazebo `living_room` world map includes `slam_toolbox` pose graph
- Fixed `localization_compare.launch.py` launching second copy of Nav2
- Fixed `localization_compare.launch.py` tracking the wrong odom ground_truth
- Enabled FastDDS shared memory
- Compared `slam_toolbox` scan matching with AMCL (linear, angular errors); tightened AMCL in `oomwoo_one/config/navigation.yaml`

### 8/15/2026

- localization A/B tooling for the "LiDAR scan vs map walls" misregistration: a new `localization_error` meter (in `oomwoo_sim_support`) scores a localizer's estimate against the sim's ground truth and logs `LOC_ERR pos/yaw` plus a windowed RMS, publishing `~/pos_err_m` / `~/yaw_err_deg` for plotting. It is localizer-agnostic — reads the `map→base` TF, or a pose topic like `/amcl_pose` with `estimate_topic:=…` — so the same meter scores AMCL and slam_toolbox alike. Run it with `odom_source:=ground_truth`
- `localization_compare.launch.py` runs **AMCL and slam_toolbox localization side by side**: slam_toolbox owns the `map→odom` TF while AMCL runs with `tf_broadcast:false` (only `/amcl_pose`), so there is no TF conflict, and two meters plot both error curves live. AMCL uses your unmodified `navigation.yaml`; slam_toolbox loads a serialized pose-graph (`mapper_params_localization.yaml`, localization mode)
  - to make the graph: map with `slam:=True`, then `ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '…/living_room_serial'}"` and `map_saver_cli` from the same session so the pgm and the graph share an origin

```
ros2 launch oomwoo_gazebo world.launch.py odom_source:=ground_truth  # :=robot_wheels
ros2 launch oomwoo_sim_support localization_compare.launch.py \
  use_sim_time:=true map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
ros2 run kaiaai_teleop teleop_keyboard
ros2 run rqt_plot rqt_plot  # add /loc_err_amcl/pos_err_m/data /loc_err_slam/pos_err_m/data
# ros2 run plotjuggler plotjuggler --layout /path/to/layout.xml
ros2 launch oomwoo_clean wall_clean_bump_out.launch.py use_sim_time:=true
```

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
  map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml rviz_config:=bump_map.rviz
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
  map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml           # auto-localizes now
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
ros2 launch oomwoo_bringup navigation.launch.py use_sim_time:=true map:=/ros_ws/src/oomwoo_gazebo/maps/living_room.yaml
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
ros2 launch oomwoo_gazebo world.launch.py odom_source:=robot_wheels  # wheel-encoder odom, slip drifts
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
