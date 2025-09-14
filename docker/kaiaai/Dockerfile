ARG distro_tag=iron
FROM osrf/ros:$distro_tag-desktop

WORKDIR /uros_ws

RUN git clone --depth 1 -b $ROS_DISTRO https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup \
&&  . /opt/ros/$ROS_DISTRO/setup.sh \
&&  apt update \
&&  apt install -y ed python3-pip \
&&  apt install -y ros-$ROS_DISTRO-rmw-fastrtps-cpp \
&&  apt remove -y ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
&&  rosdep update --rosdistro $ROS_DISTRO\
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

RUN apt install -y python3-pip nano inotify-tools \
ros-$ROS_DISTRO-gazebo-ros-pkgs ros-$ROS_DISTRO-joint-state-publisher-gui \
ros-$ROS_DISTRO-cartographer-ros \
ros-$ROS_DISTRO-nav2-map-server ros-$ROS_DISTRO-nav2-bringup \
ros-$ROS_DISTRO-joint-state-publisher ros-$ROS_DISTRO-xacro

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/kaiaai/kaiaai_msgs src/kaiaai_msgs \
&&  git clone -b dev --depth 1 https://github.com/kaiaai/kaiaai src/kaiaai \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/kaiaai/kaiaai_telemetry src/kaiaai_telemetry \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/kaiaai/kaiaai_teleop src/kaiaai_teleop \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/kaiaai/kaiaai_bringup src/kaiaai_bringup \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/makerspet/makerspet_fido src/makerspet_fido \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/makerspet/makerspet_loki src/makerspet_loki \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/makerspet/makerspet_snoopy src/makerspet_snoopy \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/makerspet/makerspet_mini src/makerspet_mini \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/makerspet/makerspet src/makerspet \
&&  git clone -b $ROS_DISTRO --depth 1 https://github.com/kaiaai/kaiaai_gazebo src/kaiaai_gazebo \
&&  git clone --depth 1 https://github.com/kaiaai/m-explore-ros2 src/m-explore-ros2 \
&&  git clone --depth 1 https://github.com/kaiaai/auto_mapper src/auto_mapper \
&&  git clone --depth 1 https://github.com/kaiaai/nav2_wfe src/nav2_wfe \
&&  colcon build --symlink-install \
&&  rm -rf log/
# rm -rf build/

RUN echo ". /opt/ros/$ROS_DISTRO/setup.bash" >> ~/.bashrc
RUN echo ". /uros_ws/install/setup.bash" >> ~/.bashrc
RUN echo ". /ros_ws/install/setup.bash" >> ~/.bashrc
# RUN echo "export KAIAAI_ROBOT=makerspet_snoopy" >> ~/.bashrc
RUN echo "alias kaia='ros2 run kaiaai cli'" >> ~/.bashrc

RUN rm /*.sh
COPY ./kaiaai-entrypoint.sh /
COPY ./.bash_history /root

RUN DEBIAN_FRONTEND=noninteractive apt install -y tigervnc-standalone-server xfce4 xfce4-terminal \
&&  mkdir ~/.vnc \
&&  echo startxfce4 > ~/.vnc/xstartup \
&&  chmod +x ~/.vnc/xstartup \
&&  apt autoremove -y \
&&  rm -rf /var/lib/apt/lists/*

EXPOSE 8888/udp
EXPOSE 5601/tcp
ENTRYPOINT ["/bin/sh", "/kaiaai-entrypoint.sh"]
CMD ["bash"]
