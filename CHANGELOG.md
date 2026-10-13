# Changelog

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
