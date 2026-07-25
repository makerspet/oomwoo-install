# Raspberry Pi Runtime Benchmark

Use this harness to measure whether the OOMWOO onboard runtime can move from a
comfortable 4 GB Pi 4/5 or CM4/CM5 profile to a lower-cost 2 GB profile without
moving SLAM or navigation off the robot.

The tool launches a workload in its own Linux process session, samples that
session through `/proc`, and writes a self-describing JSON report. It can also
attach to an already-running graph by command-line pattern. No Python packages
outside the standard library are required.

## Metrics

Each sample records:

- RSS and PSS for every selected process
- private and shared memory when `smaps_rollup` is readable
- process CPU use, where 100% represents one fully used CPU core
- system `MemAvailable`, estimated memory used, and swap used
- process names, command lines, timestamps, and sample counts

Each report also records the board model, architecture, CPU, RAM, kernel, OS,
ROS distro, RMW implementation, workload git SHA, scenario, variant, LiDAR rate,
scan-dropping policy, and custom `KEY=VALUE` metadata.

PSS is the primary graph-memory metric because ROS 2 processes share middleware
and library pages. RSS remains useful for spotting large processes, but summing
RSS over a graph double-counts shared pages.

## Install

The runtime installer places the command at:

```text
~/.local/bin/oomwoo-runtime-benchmark
```

It can also be run directly from a checkout:

```bash
python3 ubuntu/tools/oomwoo_runtime_benchmark.py --help
```

## Smoke Test With The Simulated MCU

This first run proves the collection path without ROS 2 or robot hardware:

```bash
mkdir -p ~/oomwoo_benchmarks

oomwoo-runtime-benchmark record \
  --scenario simulated_mcu_idle \
  --variant baseline \
  --settle 2 \
  --duration 30 \
  --interval 1 \
  --metadata board=pi4-2gb \
  --output ~/oomwoo_benchmarks/simulated-mcu-baseline.json \
  -- oomwoo-sim-mcu-serial --link /tmp/oomwoo-mcu-serial
```

The launched process and its descendants are stopped with `SIGINT` after the
measurement. A command that exits during the sample window is flagged in the
report and makes the command return non-zero, so a half-started ROS graph cannot
silently look efficient. The report also records the time until the first
selected process appears; this is process startup timing, not ROS graph
readiness.

## Canonical Runtime Runs

Use the same clean boot, power mode, cooling, ROS domain, RMW, bag, map, launch
arguments, settle time, measurement duration, and 5 Hz LiDAR input for baseline
and candidate runs. Record at least three repetitions of each scenario:

1. `ros_graph_idle`: onboard graph at idle.
2. `slam_5hz`: SLAM with 5 Hz LiDAR and no scan dropping.
3. `nav_known_map`: Nav2 navigating on the same saved map.

Example baseline:

```bash
source /opt/ros/jazzy/setup.bash
source ~/oomwoo_runtime_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

oomwoo-runtime-benchmark record \
  --scenario slam_5hz \
  --variant baseline \
  --lidar-hz 5 \
  --scan-dropping no \
  --settle 20 \
  --duration 120 \
  --interval 2 \
  --workspace ~/oomwoo_runtime_ws \
  --metadata cooling=active \
  --metadata power_supply=official_5v5a \
  --output ~/oomwoo_benchmarks/slam-baseline-run1.json \
  -- ros2 launch <package> <runtime-launch.py> <arguments>
```

Run the same scenario after enabling the proposed ROS 2 composition or process
layout, changing only the variant and launch command:

```bash
oomwoo-runtime-benchmark record \
  --scenario slam_5hz \
  --variant composition-candidate \
  --lidar-hz 5 \
  --scan-dropping no \
  --settle 20 \
  --duration 120 \
  --interval 2 \
  --workspace ~/oomwoo_runtime_ws \
  --metadata cooling=active \
  --metadata power_supply=official_5v5a \
  --output ~/oomwoo_benchmarks/slam-composition-run1.json \
  -- ros2 launch <package> <composed-runtime-launch.py> <arguments>
```

The placeholders are intentional until OOMWOO selects a canonical onboard
bringup launch. The exact command is retained in every report.

## Attach To A Running Graph

Use `--attach-pattern` when another service manager owns the process lifecycle:

```bash
oomwoo-runtime-benchmark record \
  --scenario nav_known_map \
  --variant baseline \
  --attach-pattern 'component_container|slam_toolbox|nav2|oomwoo' \
  --exclude 'ros2 bag|rosbag2|oomwoo_runtime_benchmark' \
  --duration 120 \
  --output ~/oomwoo_benchmarks/nav-baseline.json
```

Keep sensor drivers in the measurement when they will run onboard. Exclude a
bag player only when it stands in for external test input and document that fact
with `--metadata sensor_source=bag_excluded`.

## Compare A Candidate

The comparator writes a review-ready Markdown table and optional JSON:

```bash
oomwoo-runtime-benchmark compare \
  ~/oomwoo_benchmarks/slam-baseline-run1.json \
  ~/oomwoo_benchmarks/slam-composition-run1.json \
  --strict \
  --output ~/oomwoo_benchmarks/slam-comparison.md \
  --json-output ~/oomwoo_benchmarks/slam-comparison.json
```

`--strict` returns a non-zero status when scenario, LiDAR rate, or scan-dropping
policy differs. Hardware, RAM, ROS distro, and RMW mismatches are visible as
warnings because cross-board comparisons can still be useful, but they are not
equivalent benchmark runs.

## Interpreting The 2 GB Budget

The default target is 2048 MiB with at least 256 MiB estimated headroom. The
budget uses peak system memory pressure, not only the selected ROS processes, so
it includes the OS and other always-on services.

- `pass` or `fail`: measured on a host whose installed memory is in the target
  class.
- `indicative-pass` or `indicative-fail`: measured on a larger-memory host.

Linux changes cache and memory behavior with available RAM. Therefore an
indicative pass on a 4 GB or 16 GB board is evidence for the next experiment,
not permission to freeze a 2 GB BOM. Repeat it on a real 2 GB Pi/CM target and
confirm no swap use, thermal throttling, scan dropping, or navigation failure.

## Cost Decision Gate

Moving the production profile from 4 GB to 2 GB can reduce compute-module cost
and improve availability of lower-memory SKUs. Accept that saving only after:

- three repeatable idle, SLAM, and Nav2 runs on the target board
- no dropped 5 Hz LiDAR scans
- at least 256 MiB headroom at the worst measured phase
- no sustained swap use or thermal throttling
- live MCU serial, dock/IR homing, and required camera workload are included
- recovery and safety-adjacent behavior remains within its latency target

This makes the hardware-cost reduction a measured engineering decision rather
than a language or architecture assumption.
