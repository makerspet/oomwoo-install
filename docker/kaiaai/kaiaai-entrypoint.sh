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

# shellcheck source=/dev/null
. /etc/fastdds_profile.sh

set -e
# printf, not echo: only dash's echo expands \033: bash's would print the
# escapes literally. Byte-identical output, but portable across /bin/sh.
printf '\033[31mVisit https://github.com/makerspet/oomwoo-install for help\033[0m\n'
exec "$@"