# shellcheck shell=sh
# Single source of truth for the ROS environment in this image.
# Copied to /etc/ros_env.sh by the Dockerfile. Sourced, never executed.
#
# Wired up in three places so every shell context gets the same environment:
#
#   /root/.bashrc           -> interactive shells
#   $BASH_ENV  (Dockerfile) -> non-interactive shells, i.e. the case that used
#                              to fail: docker exec <ctr> bash -c "ros2 ..."
#   /etc/profile.d/         -> login shells
#
# The guard flag is exported, so nested shells inherit the environment and skip
# re-sourcing. That keeps PATH from growing a duplicate entry per nesting level
# and avoids paying the ~1s ROS setup cost in every child process.
if [ -z "$OOMWOO_ROS_ENV" ]; then
  # /etc/profile.d is also read by dash (login shells), which cannot parse
  # setup.bash -- so pick the POSIX variant unless we are actually in bash.
  if [ -n "$BASH_VERSION" ]; then
    _ros_env_ext='bash'
  else
    _ros_env_ext='sh'
  fi

  # stdout is kept clean so `bash -c "..."` output stays machine-parseable.
  # stderr is deliberately left alone so genuine failures still surface.
  # shellcheck source=/dev/null
  { . "/opt/ros/jazzy/setup.$_ros_env_ext"
    . "/uros_ws/install/setup.$_ros_env_ext"
    . "/ros_ws/install/setup.$_ros_env_ext"
  } > /dev/null

  unset _ros_env_ext
  export OOMWOO_ROS_ENV=1
fi
