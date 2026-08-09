#!/bin/sh
# Installed by the Dockerfile as /usr/local/bin/kaia (no extension) -- the
# user-facing CLI command. Kept as *.sh here so the repo's shellcheck and
# `bash -n` CI gates pick it up.
#
# Keep this POSIX sh: it must work when invoked directly by a bare `sh`, by a
# non-interactive shell, or from a script -- i.e. contexts where nothing has
# sourced the ROS environment yet. The guard makes sourcing a no-op when the
# environment is already set up (the common case now that the image exports
# BASH_ENV=/etc/ros_env.sh for bash).
if ! ros2 pkg prefix kaiaai >/dev/null 2>&1; then
  # shellcheck source=/dev/null
  . /opt/ros/jazzy/setup.sh
  # shellcheck source=/dev/null
  . /ros_ws/install/setup.sh
fi
exec ros2 run kaiaai cli "$@"
