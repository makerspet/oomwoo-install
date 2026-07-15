#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/oomwoo_runtime_ws}"
SKIP_BUILD=0
INSTALL_SIM_SERIAL=1

usage() {
  cat <<'EOF'
Usage:
  install_oomwoo_runtime_jazzy.sh [options]

Options:
  --workspace PATH       Runtime workspace. Default: ~/oomwoo_runtime_ws
  --skip-build           Clone/install packages but skip colcon build.
  --no-sim-serial        Do not install the simulated MCU serial helper.
  --help                 Show this help.

This script is a first Raspberry Pi 4/5 4GB runtime scaffold for OOMWOO. It
installs ROS2 Jazzy runtime packages, avoids desktop/Gazebo tooling, prepares a
minimal workspace, and installs a simulated CPU-MCU serial helper.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="${2:-}"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    --no-sim-serial)
      INSTALL_SIM_SERIAL=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$WORKSPACE" ]]; then
  echo "--workspace must not be empty" >&2
  exit 2
fi

require_ubuntu_2404() {
  if [[ ! -r /etc/os-release ]]; then
    echo "Cannot detect OS. This script currently targets Ubuntu 24.04." >&2
    exit 1
  fi
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
    echo "Warning: expected Ubuntu 24.04 for ROS2 Jazzy, got ${PRETTY_NAME:-unknown}." >&2
  fi
}

install_ros_apt_source() {
  sudo apt update
  sudo apt install -y software-properties-common curl gnupg lsb-release
  sudo add-apt-repository universe -y
  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo "$UBUNTU_CODENAME") main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
}

install_runtime_packages() {
  sudo apt update
  sudo apt install -y \
    build-essential \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    python3-serial \
    python3-vcstool \
    ros-dev-tools \
    ros-jazzy-nav2-bringup \
    ros-jazzy-navigation2 \
    ros-jazzy-rmw-fastrtps-cpp \
    ros-jazzy-robot-localization \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros-base \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-slam-toolbox \
    ros-jazzy-tf2-ros \
    ros-jazzy-xacro
}

init_rosdep_if_needed() {
  if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
    sudo rosdep init
  fi
  rosdep update --rosdistro jazzy
}

clone_or_update() {
  local branch="$1"
  local url="$2"
  local path="$3"

  if [[ -d "$path/.git" ]]; then
    git -C "$path" fetch --depth 1 origin "$branch"
    git -C "$path" checkout "$branch"
    git -C "$path" reset --hard "origin/$branch"
  else
    git clone -b "$branch" --depth 1 "$url" "$path"
  fi
}

prepare_workspace() {
  mkdir -p "$WORKSPACE/src"

  clone_or_update jazzy https://github.com/kaiaai/kaiaai_msgs "$WORKSPACE/src/kaiaai_msgs"
  clone_or_update jazzy https://github.com/kaiaai/kaiaai "$WORKSPACE/src/kaiaai"
  clone_or_update jazzy https://github.com/kaiaai/kaiaai_bringup "$WORKSPACE/src/kaiaai_bringup"
  clone_or_update jazzy https://github.com/makerspet/makerspet_vac "$WORKSPACE/src/makerspet_vac"
  clone_or_update jazzy https://github.com/makerspet/makerspet "$WORKSPACE/src/makerspet"
  clone_or_update main https://github.com/makerspet/oomwoo-one "$WORKSPACE/src/oomwoo_one"
  clone_or_update jazzy https://github.com/remakeai/vacuum_ros2_bridge "$WORKSPACE/src/vacuum_ros2_bridge"
  clone_or_update jazzy https://github.com/kaiaai/nav2_wfe "$WORKSPACE/src/nav2_wfe"
  clone_or_update jazzy https://github.com/kaiaai/auto_mapper "$WORKSPACE/src/auto_mapper"
  clone_or_update jazzy https://github.com/kaiaai/m-explore-ros2 "$WORKSPACE/src/m-explore-ros2"
}

build_workspace() {
  # ROS 2's setup.bash dereferences unset variables (AMENT_TRACE_SETUP_FILES),
  # which aborts the script under the `set -u` above. Relax it for the source.
  set +u
  . /opt/ros/jazzy/setup.bash
  set -u
  cd "$WORKSPACE"
  rosdep install --from-paths src --ignore-src -y
  colcon build --symlink-install
  rm -rf log/
}

install_sim_serial() {
  if [[ "$INSTALL_SIM_SERIAL" -eq 0 ]]; then
    return
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  mkdir -p "$HOME/.local/bin"
  install -m 0755 "$script_dir/tools/oomwoo_sim_mcu_serial.py" \
    "$HOME/.local/bin/oomwoo-sim-mcu-serial"
}

update_bashrc() {
  local marker="# OOMWOO runtime Jazzy"
  if grep -q "$marker" "$HOME/.bashrc" 2>/dev/null; then
    return
  fi

  cat >> "$HOME/.bashrc" <<EOF

$marker
source /opt/ros/jazzy/setup.bash
if [ -f "$WORKSPACE/install/setup.bash" ]; then
  source "$WORKSPACE/install/setup.bash"
fi
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export OOMWOO_MCU_SERIAL=/tmp/oomwoo-mcu-serial
export PATH="\$HOME/.local/bin:\$PATH"
EOF
}

main() {
  require_ubuntu_2404
  install_ros_apt_source
  install_runtime_packages
  init_rosdep_if_needed
  prepare_workspace
  install_sim_serial

  if [[ "$SKIP_BUILD" -eq 0 ]]; then
    build_workspace
  fi

  update_bashrc

  cat <<EOF

OOMWOO Jazzy runtime scaffold installed.

Workspace: $WORKSPACE
Simulated MCU serial:
  oomwoo-sim-mcu-serial --link /tmp/oomwoo-mcu-serial

Open a new shell or run:
  source ~/.bashrc
EOF
}

main "$@"
