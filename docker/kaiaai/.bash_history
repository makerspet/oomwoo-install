exit
ros2 launch kaiaai_bringup navigation.launch.py use_sim_time:=true map:=/ros_ws/src/kaiaai_gazebo/map/living_room.yaml
ros2 launch kaiaai_bringup navigation.launch.py use_sim_time:=true slam:=True
ros2 launch kaiaai_gazebo world.launch.py
ros2 param set /pet lidar.scan.freq.target 7.0
ros2 launch kaiaai_bringup navigation.launch.py map:=$HOME/maps/map.yaml
ros2 run nav2_map_server map_saver_cli -f ~/maps/map --ros-args -p save_map_timeout:=60.0
ros2 launch explore_lite explore.launch.py
ros2 launch kaiaai_bringup navigation.launch.py slam:=True
ros2 launch kaiaai_bringup monitor_robot.launch.py
ros2 run kaiaai_teleop teleop_keyboard
ros2 launch kaiaai_bringup physical.launch.py
ros2 launch vacuum_ros2_bridge bridge.launch.py
kaia config robot.model proscenic_m6pro
