# Open source vacuum cleaner robot - Docker and Ubuntu install

Tutorials:
- Install/use OOMWOO software development environment [in simulation](https://makerspet.com/blog/simulate-the-proscenic-m6-pro-robot-vacuum-in-gazebo-with-ros-2/) (no hardware needed).
- Install/use OOMWOO software development environment using a real (temp placeholder) vacuum cleaner
[Part 1](https://makerspet.com/blog/tutorial-connect-robot-vacuum-cleaner-to-ros-2-proscenic-m6-pro/) and [Part 2](https://makerspet.com/blog/tutorial-part-2-drive-map-navigate-your-proscenic-m6-pro-in-ros-2/).

Visit [main project repo](https://github.com/makerspet/oomwoo).

![oomwoo Open source vacuum cleaner placeholder illustration](https://github.com/makerspet/oomwoo/raw/main/assets/vacuum-no-dock-front.webp)

## Raspberry Pi runtime

The current Docker image is a desktop development environment. For onboard robot
work, see the lighter Raspberry Pi runtime scaffold:

- [Raspberry Pi install script](ubuntu/install_oomwoo_runtime_jazzy.sh)
- [simulated MCU serial I/O](ubuntu/tools/oomwoo_sim_mcu_serial.py)

## Release history

### 7/21/2026
- clean using an existing map; Boustrophedon, clunky, slow, fails often
  - packages in makerspet/oomwoo-ros2-tools
- added bumpers, verified working
- added localization (kidnapped robot); not tested
- forked kaiaai_gazebo, kaiaai_bringup to oomwoo_gazebo, oomwoo_bringup

### 7/8/2026
- added a first Raspberry Pi 4/5 4GB runtime install plan
- added simulated CPU-MCU serial I/O placeholder

### 7/1/2026
- added oomwoo-one ROS2 robot description package (simulation only)

### 6/26/2026
- added https://github.com/remakeai/vacuum_ros2_bridge
  - LiDAR compute moved to vacuum_ros2_bridge

### 6/18/2026
- added bumper sensors for proscenic-m6pro
- fixed Gazebo living world marble table collision mesh

### 6/16/2026
- added Proscenic M6 Pro [robot description](https://github.com/makerspet/proscenic-m6pro)
  - `kaia config robot.model proscenic_m6pro`
