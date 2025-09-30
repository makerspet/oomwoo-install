. "/opt/ros/$ROS_DISTRO/setup.sh"
. "/uros_ws/install/local_setup.sh"

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