# Changelog

## 2026-10-19 — `makerspet/oomwoo:jazzy-dev`

- **Lighter Nav2.** `navigation.launch.py` with slam_toolbox localization (the
  default) now starts only the Nav2 servers OOMWOO uses: controller, planner,
  behaviors, BT navigator, velocity smoother and collision monitor. The route,
  docking, waypoint and path smoother servers are gone.
- **Nav2 config** (`oomwoo_one/config/navigation.yaml`): no voxel layers in the
  costmaps, which with a 2D LiDAR only repeated the obstacle layer's work, and a
  1 s lifecycle bond heartbeat instead of 0.1 s.
- Together these cut Nav2's idle CPU about 20%, on a laptop and on a phone. The
  robot still reaches its goals in the simulation, with slam_toolbox and with
  AMCL localization. Details: [ROS 2 on a smartphone](https://makerspet.com/blog/oomwoo-smartphone-ros2-termux/#oomwoo-navigation-stack).
- Rebuilt from the latest `jazzy` of every bundled repo.

Update with `docker pull makerspet/oomwoo:jazzy-dev`.

## 2026-10-12 — `makerspet/oomwoo:jazzy-dev`

- **New vacuum_ros2_bridge.** It reads each robot's wheel and IMU scales from
  SangamIO, so the same image drives the Proscenic M6 Pro and the Roborock
  S5 Max. The S5 Max has no robot description (URDF) yet, so only the bridge
  works for it.
- **Corrected CRL-200S gyro scale** in the bridge. For a correct `/imu` yaw on a
  Proscenic M6 Pro, also update SangamIO and its config; see the
  [VacuumTiger changelog](https://github.com/kaiaai/VacuumTiger/blob/main/CHANGELOG.md).
- Rebuilt from the latest `jazzy` of every bundled repo.

Update with `docker pull makerspet/oomwoo:jazzy-dev`.
