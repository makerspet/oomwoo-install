#!/bin/sh
# Invoked by the image as: ENTRYPOINT ["/bin/sh", "/kaiaai-entrypoint.sh"]
# Keep this POSIX sh -- the shebang declares the dialect for linting; the
# explicit interpreter in ENTRYPOINT is what actually runs it.
. "/opt/ros/$ROS_DISTRO/setup.sh"
. "/uros_ws/install/local_setup.sh"
. "/ros_ws/install/local_setup.sh"

if [ "$MICROROS_DISABLE_SHM" = "1" ] ; then
    if [ "$ROS_LOCALHOST_ONLY" = "1" ] ; then
        export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/disable_fastdds_shm_localhost_only.xml
    else
        export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/disable_fastdds_shm.xml
    fi
fi

set -e
echo "\033[31mVisit https://github.com/kaiaai/kaiaai for help\033[0m"
exec "$@"