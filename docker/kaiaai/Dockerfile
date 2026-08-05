FROM osrf/ros:jazzy-desktop

WORKDIR /uros_ws

RUN git clone -b jazzy --depth 1 https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup \
&&  . /opt/ros/jazzy/setup.sh \
&&  apt update \
&&  apt install -y ed python3-pip \
&&  apt install -y ros-jazzy-rmw-fastrtps-cpp \
&&  apt remove -y ros-jazzy-rmw-cyclonedds-cpp \
&&  rosdep update --rosdistro jazzy\
&&  rosdep install --from-paths src --ignore-src -y \
&&  colcon build \
&&  . install/local_setup.sh \
&&  ros2 run micro_ros_setup create_agent_ws.sh \
&&  ros2 run micro_ros_setup build_agent.sh \
&&  rm -rf log/ build/ src/

# Disable shared memory
COPY disable_fastdds_shm.xml disable_fastdds_shm_localhost_only.xml /tmp/

ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV MICROROS_DISABLE_SHM=1

WORKDIR /ros_ws

RUN apt install -y nano inotify-tools \
ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-ros2-control \
ros-jazzy-ros2-controllers ros-jazzy-joint-state-publisher-gui \
ros-jazzy-cartographer-ros ros-jazzy-joint-state-publisher ros-jazzy-xacro \
ros-jazzy-nav2-map-server ros-jazzy-nav2-bringup python3-websockets \
ros-jazzy-navigation2 python3-socketio python3-aiohttp python3-httpx \
python3-click python3-flask ros-jazzy-robot-localization

RUN apt update && apt upgrade -y

# apt update && apt install -y ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations

RUN . /opt/ros/jazzy/setup.sh \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_msgs src/kaiaai_msgs \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai src/kaiaai \
&&  git clone -b jazzy --depth 1 https://github.com/remakeai/remake-ros2 src/remake-ros2 \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_telemetry src/kaiaai_telemetry \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_teleop src/kaiaai_teleop \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/oomwoo_bringup src/oomwoo_bringup \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_mini src/makerspet_mini \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/proscenic-m6pro src/proscenic-m6pro \
&&  git clone -b main --depth 1 https://github.com/makerspet/oomwoo-one src/oomwoo_one \
&&  git clone -b jazzy --depth 1 https://github.com/remakeai/vacuum_ros2_bridge src/vacuum_ros2_bridge \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet src/makerspet \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/oomwoo_gazebo src/oomwoo_gazebo \
&&  git clone -b main --depth 1 https://github.com/makerspet/oomwoo-ros2-tools src/oomwoo-ros2-tools \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/m-explore-ros2 src/m-explore-ros2 \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/auto_mapper src/auto_mapper \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/nav2_wfe src/nav2_wfe \
&&  rosdep install --from-paths src --ignore-src -y \
&&  colcon build --symlink-install \
&&  rm -rf log/
# rm -rf build/

WORKDIR /ros_ws/src
RUN find . -type d -name ".git" -exec rm -rf {} +

# Install Remake SDK (CLI, Socket.IO client for ROS2 bridge)
# Note: Using [ros2] extra - no podman needed inside container
WORKDIR /root
RUN git clone -b main https://github.com/remakeai/remake-sdk \
&&  pip install --break-system-packages -e "remake-sdk[ros2]" \
&&  rm -rf remake-sdk/.git

# Create maps directory
RUN mkdir -p ~/maps

WORKDIR /ros_ws

RUN echo ". /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo ". /uros_ws/install/setup.bash" >> ~/.bashrc
RUN echo ". /ros_ws/install/setup.bash" >> ~/.bashrc
# RUN echo "alias remake='ros2 run remakeai remake'" >> ~/.bashrc

# 'kaia' as a real command on PATH so it works in every shell context --
# interactive, non-interactive, scripts, agents, CI.
RUN printf '%s\n' \
    '#!/bin/sh' \
    'if ! ros2 pkg prefix kaiaai >/dev/null 2>&1; then' \
    '  . /opt/ros/jazzy/setup.sh' \
    '  . /ros_ws/install/setup.sh' \
    'fi' \
    'exec ros2 run kaiaai cli "$@"' \
    > /usr/local/bin/kaia \
 && chmod +x /usr/local/bin/kaia

RUN rm /*.sh
COPY ./kaiaai-entrypoint.sh /
COPY ./.bash_history /root
COPY ./.kaiaai.yaml /root

EXPOSE 8888/udp
EXPOSE 8788/tcp
# EXPOSE 5601/tcp
ENTRYPOINT ["/bin/sh", "/kaiaai-entrypoint.sh"]
CMD ["bash"]
