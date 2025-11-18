FROM osrf/ros:jazzy-desktop

WORKDIR /uros_ws

RUN git clone --depth 1 -b jazzy https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup \
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
ros-jazzy-ros-gz \
ros-jazzy-gz-ros2-control \
ros-jazzy-ros2-control \
ros-jazzy-ros2-controllers \
ros-jazzy-joint-state-publisher-gui \
ros-jazzy-cartographer-ros \
# ros-jazzy-nav2-map-server ros-jazzy-nav2-bringup \
ros-jazzy-joint-state-publisher ros-jazzy-xacro \
apt install ros-jazzy-nav2* \
python3-websockets

# apt update && apt install -y ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations

RUN . /opt/ros/jazzy/setup.sh \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_msgs src/kaiaai_msgs \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai src/kaiaai \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_telemetry src/kaiaai_telemetry \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_teleop src/kaiaai_teleop \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_bringup src/kaiaai_bringup \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_fido src/makerspet_fido \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_loki src/makerspet_loki \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_snoopy src/makerspet_snoopy \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_mini src/makerspet_mini \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet_vac src/makerspet_vac \
&&  git clone -b jazzy --depth 1 https://github.com/makerspet/makerspet src/makerspet \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/kaiaai_gazebo src/kaiaai_gazebo \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/m-explore-ros2 src/m-explore-ros2 \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/auto_mapper src/auto_mapper \
&&  git clone -b jazzy --depth 1 https://github.com/kaiaai/nav2_wfe src/nav2_wfe \
&&  rosdep install --from-paths src --ignore-src -y \
&&  colcon build --symlink-install \
&&  rm -rf log/
# rm -rf build/

RUN echo ". /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo ". /uros_ws/install/setup.bash" >> ~/.bashrc
RUN echo ". /ros_ws/install/setup.bash" >> ~/.bashrc
# RUN echo "export KAIAAI_ROBOT=makerspet_snoopy" >> ~/.bashrc
RUN echo "alias kaia='ros2 run kaiaai cli'" >> ~/.bashrc

RUN rm /*.sh
COPY ./kaiaai-entrypoint.sh /
COPY ./.bash_history /root

EXPOSE 8888/udp
# EXPOSE 5601/tcp
ENTRYPOINT ["/bin/sh", "/kaiaai-entrypoint.sh"]
CMD ["bash"]