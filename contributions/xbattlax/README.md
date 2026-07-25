# OOMWOO health monitor

Status: optional, self-hosted contribution. This package is not part of the
official OOMWOO runtime image while the maintainers evaluate the health
monitoring design.

The source and releases are maintained at
[`xbattlax/health-monitor`](https://github.com/xbattlax/health-monitor). The
installer in this directory fetches the stable `v0.1.0` release and builds its
ROS 2 package without modifying the official OOMWOO installer or Docker image.

## What it does

`oomwoo_health_monitor` aggregates component heartbeats into a stack-health
state and emits the MCU heartbeat only while every required component is
healthy. It provides:

- a versioned component roster
- bounded heartbeat deadlines based on a shared ROS clock
- aggregate stack state and diagnostics
- suppression of the MCU heartbeat when a critical component becomes stale
- a deterministic simulator and unit tests in the self-hosted repository

This is a software deadman layer. Motor shutdown, bumper/cliff/wheel-drop
handling, overcurrent protection, and the final CPU-heartbeat timeout remain
MCU-owned safety functions.

## Prerequisites

- Ubuntu 24.04
- ROS 2 Jazzy installed under `/opt/ros/jazzy`
- `git`, `python3-colcon-common-extensions`, and `python3-rosdep`

For example:

```bash
sudo apt update
sudo apt install git python3-colcon-common-extensions python3-rosdep
```

## Install

From a clone of `makerspet/oomwoo-install`:

```bash
bash contributions/xbattlax/install.sh
source "$HOME/oomwoo_health_monitor_ws/install/setup.bash"
ros2 launch oomwoo_health_monitor health_monitor.launch.py
```

To add the package to an existing OOMWOO runtime workspace:

```bash
bash contributions/xbattlax/install.sh \
  --workspace "$HOME/oomwoo_runtime_ws"
```

The script:

1. clones or refreshes the self-hosted source in `<workspace>/src/health-monitor`
2. checks out the requested ref in detached-HEAD mode
3. installs missing package dependencies with `rosdep`
4. builds only `oomwoo_health_monitor` with `colcon`

It refuses to replace a source checkout that has local changes or a different
`origin` URL.

Use another release or test branch only intentionally:

```bash
bash contributions/xbattlax/install.sh --ref v0.1.0
```

Run `bash contributions/xbattlax/install.sh --help` for all options.

## Verify

The self-hosted release includes unit tests and a deterministic simulator. This
contribution also carries a dependency-free installer regression test:

```bash
bash contributions/xbattlax/test_install.sh
```

The test proves release pinning, detached checkout, idempotent reinstall, and
the dirty-checkout protection without requiring ROS 2 or network access.

## Remove

The installer writes only inside the selected colcon workspace. Remove the
source and rebuild that workspace to uninstall the optional package:

```bash
rm -rf "$HOME/oomwoo_health_monitor_ws"
```
