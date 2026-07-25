#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/oomwoo_health_monitor_ws}"
HEALTH_MONITOR_REF="${OOMWOO_HEALTH_MONITOR_REF:-v0.1.0}"
HEALTH_MONITOR_REPOSITORY="${OOMWOO_HEALTH_MONITOR_REPOSITORY:-https://github.com/xbattlax/health-monitor.git}"
ROS_SETUP="${OOMWOO_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
RUN_ROSDEP=1
RUN_BUILD=1

usage() {
  cat <<'EOF'
Usage:
  install.sh [options]

Options:
  --workspace PATH     Colcon workspace. Default: ~/oomwoo_health_monitor_ws
  --ref REF            Git release, branch, or commit. Default: v0.1.0
  --repository URL     Source repository or mirror.
  --ros-setup PATH     ROS setup file. Default: /opt/ros/jazzy/setup.bash
  --skip-rosdep        Do not run rosdep.
  --skip-build         Fetch the source but do not run colcon.
  --help               Show this help.

The default path fetches the self-hosted v0.1.0 release, resolves dependencies,
and builds only oomwoo_health_monitor. Existing source changes are never
discarded.
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      [[ $# -ge 2 ]] || fail "--workspace requires a path"
      WORKSPACE="$2"
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || fail "--ref requires a value"
      HEALTH_MONITOR_REF="$2"
      shift 2
      ;;
    --repository)
      [[ $# -ge 2 ]] || fail "--repository requires a URL"
      HEALTH_MONITOR_REPOSITORY="$2"
      shift 2
      ;;
    --ros-setup)
      [[ $# -ge 2 ]] || fail "--ros-setup requires a path"
      ROS_SETUP="$2"
      shift 2
      ;;
    --skip-rosdep)
      RUN_ROSDEP=0
      shift
      ;;
    --skip-build)
      RUN_BUILD=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$WORKSPACE" ]] || fail "workspace must not be empty"
[[ -n "$HEALTH_MONITOR_REF" ]] || fail "ref must not be empty"
[[ -n "$HEALTH_MONITOR_REPOSITORY" ]] || fail "repository must not be empty"
command -v git >/dev/null 2>&1 || fail "git is required"

SOURCE_DIR="$WORKSPACE/src/health-monitor"

fetch_source() {
  local actual_origin resolved_commit

  mkdir -p "$WORKSPACE/src"
  if [[ -e "$SOURCE_DIR" && ! -d "$SOURCE_DIR/.git" ]]; then
    fail "$SOURCE_DIR exists but is not a Git checkout"
  fi

  if [[ -d "$SOURCE_DIR/.git" ]]; then
    if [[ -n "$(git -C "$SOURCE_DIR" status --porcelain)" ]]; then
      fail "$SOURCE_DIR has local changes; refusing to overwrite them"
    fi
    actual_origin="$(git -C "$SOURCE_DIR" remote get-url origin)"
    if [[ "$actual_origin" != "$HEALTH_MONITOR_REPOSITORY" ]]; then
      fail "$SOURCE_DIR origin is $actual_origin, expected $HEALTH_MONITOR_REPOSITORY"
    fi
  else
    git clone --no-checkout "$HEALTH_MONITOR_REPOSITORY" "$SOURCE_DIR"
  fi

  git -C "$SOURCE_DIR" fetch --force --depth 1 origin "$HEALTH_MONITOR_REF"
  resolved_commit="$(git -C "$SOURCE_DIR" rev-parse --verify 'FETCH_HEAD^{commit}')"
  git -C "$SOURCE_DIR" checkout --detach "$resolved_commit"

  printf 'Health monitor source: %s (%s)\n' \
    "$HEALTH_MONITOR_REF" "$resolved_commit"
}

build_package() {
  command -v colcon >/dev/null 2>&1 || fail "colcon is required"
  [[ -f "$ROS_SETUP" ]] || fail "ROS setup not found: $ROS_SETUP"

  set +u
  # shellcheck disable=SC1090
  source "$ROS_SETUP"
  set -u

  if [[ "$RUN_ROSDEP" -eq 1 ]]; then
    command -v rosdep >/dev/null 2>&1 || fail "rosdep is required"
    rosdep install --from-paths "$SOURCE_DIR" --ignore-src -r -y
  fi

  (
    cd "$WORKSPACE"
    colcon build \
      --base-paths "$SOURCE_DIR" \
      --packages-select oomwoo_health_monitor \
      --symlink-install
  )

  [[ -f "$WORKSPACE/install/setup.bash" ]] ||
    fail "colcon completed without creating install/setup.bash"
}

fetch_source

if [[ "$RUN_BUILD" -eq 1 ]]; then
  build_package
  cat <<EOF

oomwoo_health_monitor installed.

Activate:
  source "$WORKSPACE/install/setup.bash"

Run:
  ros2 launch oomwoo_health_monitor health_monitor.launch.py
EOF
else
  echo "Build skipped. Source is available at $SOURCE_DIR"
fi
