#!/bin/sh
# Installed by the Dockerfile as /usr/local/bin/kaia (no extension) -- the
# user-facing CLI command. Kept as *.sh here so the repo's shellcheck and
# `bash -n` CI gates pick it up.
#
# Keep this POSIX sh: it must work when invoked directly by a bare `sh`, by a
# non-interactive shell, or from a script -- i.e. contexts where nothing has
# sourced the ROS environment yet. In that case it falls back to
# /etc/ros_env.sh, the same single source of truth used by ~/.bashrc, $BASH_ENV
# and /etc/profile.d, so there is one definition of "the ROS environment" in
# the image rather than a second copy here.
if ! ros2 pkg prefix kaiaai >/dev/null 2>&1; then
  # The check above already proved the environment is unusable, so clear
  # ros_env.sh's guard flag -- otherwise a stale exported OOMWOO_ROS_ENV would
  # make it short-circuit and source nothing.
  unset OOMWOO_ROS_ENV
  # shellcheck source=/dev/null
  . /etc/ros_env.sh
fi
exec ros2 run kaiaai cli "$@"
