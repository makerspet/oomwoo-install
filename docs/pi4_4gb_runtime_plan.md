# Raspberry Pi 4/5 4GB Runtime Plan

This document sketches the first runtime path for running OOMWOO onboard on a
Raspberry Pi 4/5 or CM4/CM5-class module with 4 GB RAM, then measuring how far
the stack can be reduced toward a 2 GB target.

The desktop Docker image remains useful for development and simulation. This
runtime profile is for the robot computer: ROS2, SLAM, Nav2, LiDAR, high-level
behavior, and a serial link to an MCU that owns motors, sensors, battery/charging
supervision, watchdogs, and safety reactions.

## Goals

- Keep SLAM and navigation onboard for the consumer vacuum profile.
- Start with a Pi 4/5 or CM4/CM5 4 GB runtime baseline.
- Avoid Gazebo, desktop GUI tools, and development-only packages on the robot.
- Add a simulated CPU-MCU serial interface until the real I/O board is ready.
- Measure RSS/PSS/CPU before attempting 2 GB optimization.
- Try ROS2 composition and launch/process layout before adding new language
  dependencies.
- Keep Rust/rclrs as an optional later experiment for selected memory-heavy or
  latency-sensitive nodes.

## Non-Goals For This First Scaffold

- It does not replace the desktop Docker development image.
- It does not provide a final production image.
- It does not choose the final MCU firmware protocol.
- It does not attempt Kilted, Lyrical, or Rolling yet.
- It does not provide a costed hardware BOM; that belongs with the PCB design.

## Runtime Package Direction

Install ROS2 Jazzy from Debian packages, but prefer `ros-jazzy-ros-base` plus the
robot packages that are actually needed:

- Nav2 and Nav2 bringup
- slam_toolbox
- robot_state_publisher and xacro
- robot_localization
- tf2 tools used by launch/runtime
- ros2_control and controllers when hardware interfaces need them
- Fast DDS RMW, matching the current development image direction
- Python serial tooling for the simulated MCU link

Avoid in the first runtime profile:

- `ros-jazzy-desktop`
- Gazebo / ros_gz packages
- GUI joint-state tools
- simulation worlds
- unrelated robot model packages
- telemetry or web UI pieces until a runtime measurement requires them

## Simulated CPU-MCU Serial Link

Until the OOMWOO I/O board firmware exists, run:

```bash
python3 ubuntu/tools/oomwoo_sim_mcu_serial.py --link /tmp/oomwoo-mcu-serial
```

The tool creates a pseudo-terminal symlink such as:

```text
/tmp/oomwoo-mcu-serial
```

ROS2 bridge code can open that path as if it were the MCU serial device. The
simulator emits newline-delimited JSON heartbeat/sensor frames and accepts simple
command lines, replying with acknowledgements.

This keeps the CPU-MCU contract testable while the real STM32G070 firmware and
custom serial protocol are still being designed.

## First Install Script

The first scaffold is:

```bash
ubuntu/install_oomwoo_runtime_jazzy.sh
```

It is intentionally conservative:

- installs ROS2 Jazzy runtime packages
- creates `~/oomwoo_runtime_ws`
- clones a minimal set of OOMWOO/Kaia.ai runtime repositories
- optionally builds the workspace
- installs the simulated MCU serial tool to `~/.local/bin`
- writes a runtime environment snippet to `~/.bashrc`

Run:

```bash
bash ubuntu/install_oomwoo_runtime_jazzy.sh
```

Use `--skip-build` when iterating on the script or testing package selection.

## Measurement Plan

After the runtime install works on a 4 GB board:

1. Boot cleanly and record baseline memory after login.
2. Source ROS2 and the runtime workspace.
3. Start the simulated MCU serial tool.
4. Launch the minimal OOMWOO runtime graph.
5. Record RSS/PSS/CPU for idle.
6. Run SLAM with 5 Hz LiDAR input and no scan dropping.
7. Run navigation on a known map.
8. Repeat after ROS2 composition/process-layout changes.
9. Only then decide whether a C++ or Rust/rclrs port is justified.

The related benchmark scaffold lives in:

```text
makerspet/oomwoo/contributions/compute-benchmark
```

## Path Toward 2 GB

The 2 GB target should be treated as an optimization target, not an assumption.

Suggested order:

1. Remove development/simulation packages from the runtime image.
2. Measure the Python/C++ baseline.
3. Try ROS2 composition where supported.
4. Reduce launch/process count.
5. Remove unused web/telemetry/UI pieces from the onboard profile.
6. Consider C++ ports for memory-heavy custom nodes.
7. Consider Rust/rclrs ports only after the Jazzy setup is reproducible.

## Future Branches

The maintainer mentioned interest in Kilted, Lyrical, and Rolling branches. A
good later contribution is to parameterize this script or create branch-specific
variants once the Jazzy runtime profile is validated.
