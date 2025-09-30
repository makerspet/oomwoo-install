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

RUN echo ". /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo ". /uros_ws/install/setup.bash" >> ~/.bashrc

COPY ./micro-ros_entrypoint.sh /
COPY ./.bash_history /root

EXPOSE 8888/udp
# EXPOSE 5601/tcp
ENTRYPOINT ["/bin/sh", "/micro-ros_entrypoint.sh"]
CMD ["bash"]
