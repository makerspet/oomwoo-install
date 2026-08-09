#!/bin/sh
# Invoked by the image as: ENTRYPOINT ["/bin/sh", "/kaiaai-entrypoint.sh"]
# Keep this POSIX sh -- the shebang declares the dialect for linting; the
# explicit interpreter in ENTRYPOINT is what actually runs it.
# shellcheck source=/dev/null
. "/opt/ros/$ROS_DISTRO/setup.sh"
# shellcheck source=/dev/null
. "/uros_ws/install/local_setup.sh"
# shellcheck source=/dev/null
. "/ros_ws/install/local_setup.sh"

if [ "$MICROROS_DISABLE_SHM" = "1" ] ; then
    if [ "$ROS_LOCALHOST_ONLY" = "1" ] ; then
        export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/disable_fastdds_shm_localhost_only.xml
    else
        export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/disable_fastdds_shm.xml
    fi
fi

set -e
# printf, not echo: only dash's echo expands \033: bash's would print the
# escapes literally. Byte-identical output, but portable across /bin/sh.
printf '\033[31mVisit https://github.com/makerspet/oomwoo-install for help\033[0m\n'
exec "$@"