# Kaia.ai Docker images

[Kaia.ai](https://kaiaai) is a software platform for ROS2-based pet robots. Please sign up for an early launch invite [here](https://remake.ai).

Questions? Please visit the [Support Forum](https://github.com/makerspet/support/discussions/)!

Three ways to install:
- on a Ubuntu 22.04 PC directly - easiest
- on a Ubuntu or Windows PC using Docker - recommended
- on a Ubuntu or Windows PC using a virtual machine

## Install on Ubuntu PC directly
Make sure your Ubuntu version is 22.x
```
git clone --depth 1 https://github.com/kaiaai/install
cd install/ubuntu
source install_ros2_iron_ubuntu_22_04.sh
source install_kaiaai_iron_ubuntu_22_04.sh
```

## Install on a Ubuntu or Windows PC using a virtual machine
- install [VMware Workstation](https://blogs.vmware.com/workstation/2024/05/vmware-workstation-pro-now-available-free-for-personal-use.html)
- download a [Ubuntu image](https://ubuntu.com/download/desktop) and create a virtual machine
- inside the Ubuntu virtual machine
  - run the Install-on-Ubuntu-PC-directly instructions above
  - or run install-using-Docker instructions below

## Install on Ubuntu or Windows PC using Docker
- If you are using a Windows PC, read this [blog post](https://kaia.ai/blog/local-pc-setup-windows/)
  - install [Windows WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install)
  - install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - install [VcXsrv](https://sourceforge.net/projects/vcxsrv/), launch it and set display to `0` (zero)
- When using a Linux PC
  - install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) or
[Docker Desktop](https://docs.docker.com/desktop/install/linux-install/) (with GUI)

On Ubuntu you can run
```
git clone --depth 1 https://github.com/kaiaai/install
cd install/utils
source install_docker_on_ubuntu.sh
```

<a href="http://www.youtube.com/watch?feature=player_embedded&v=XOc5kCE3MC0" target="_blank">
 <img src="http://img.youtube.com/vi/XOc5kCE3MC0/maxresdefault.jpg" alt="Robot Arduino firmware, ROS2/Docker PC setup instructions video" width="720" height="405" border="10" />
</a>

### Download Latest Pre-Built Image
- Docker Hub [image](https://hub.docker.com/r/kaiaai/kaiaai)
  - Ubuntu `sudo docker pull kaiaai/kaiaai:iron`
  - Windows command line `docker pull kaiaai/kaiaai:iron`

### Run Kaia.ai (create a container)
- on Windows
  - open a command line window (or PowerShell or terminal)
  - `cd` to `docker\utils\`
  - launch container `.\create_container_iron.cmd`
  - open another command line window, `cd` to `docker\utils\`
  - launch an extra bash session `.\launch_bash.cmd`
  - be sure to install 
- on Ubuntu
  - open a bash window
  - `cd` to `docker\utils\`
  - launch container `source create_container_iron.sh`


# Advanced - how to rebuild images

## log in to Docker Hub
```
sudo docker login -u your_docker_hub_username
```

## Build image - Linux
- install [Docker for Linux](https://docs.docker.com/engine/install/ubuntu/)
- clone the Kaia.ai Docker repo and run the command below
```
git clone https://github.com/kaiaai/install
cd install/docker
source utils/build_iron.sh
```

## Build all images - Windows
- install [Docker for Windows](https://docs.docker.com/desktop/install/windows-install/)
- clone the Kaia.ai Docker repo and run the command below
```
git clone https://github.com/kaiaai/install
cd install\docker
.\utils\build_iron.cmd
# .\utils\attest_iron.cmd
```

## Release history

### 7/21/2025
- added VNC server and Xfce, see https://github.com/makerspet/support/discussions/48

When using VNC instead of X server, run kaiaai/kaiaai docker image as follows in Windows:
```
docker run --name makerspet -it --rm -v c:\maps:/root/maps -p 8888:8888/udp -p 4430:4430/tcp -p 5901:5901 -e DISPLAY=:1 kaiaai/kaiaai:iron
```

Launch the VNC server inside the Docker container. You will be prompted to choose a VNC password.
```
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no
```

Install a VNC viewer, e.g. https://www.tightvnc.com/ on your Windows or MacOS PC.

Launch the VNC viewer. Open `localhost:5061` and enter your VNC password.

### 3/10/2025
- major bugfix: Delta, Delta-2G LiDARs decoding in kaiaai_telemetry package
- matching [Kaia.ai firmware](https://github.com/kaiaai/firmware) release v0.8.3
- image tag `kaiaai/kaiaai-031125:iron` https://hub.docker.com/repository/docker/kaiaai/kaiaai-031125

### 3/9/2025
- fixed LiDAR model names in `telem.yaml`
- mapped `/root/maps` to host
- added map save, map load and explore_lite to command history

### 12/29/2024
- dropping support for ROS2 `humble` because it is EOL
  - switched builds to `iron`

### 12/2/2024
- fixed .bash_history

### 11/21/2024
- added .bash_history with common commands for convenience

### 11/20/2024
- 12V 200RPM N20 motors for Mini

### 9/19/2024
- build with attestation

### 4/13/2024
- `docker pull kaiaai/kaiaai:humble-04-13-2024`
- `docker pull kaiaai/kaiaai:iron-04-13-2024`
- fixed a webserver script crash

### 3/27/2024
- `docker pull kaiaai/kaiaai:humble-03-27-2024`
- `docker pull kaiaai/kaiaai:iron-03-27-2024`
- changed naming from `kaiaai-ros-dev` to `kaiaai`
- added Camsense X1 LiDAR

### 3/15/2024
- changed default image name to kaiaai/kaiaai from kaiaai/kaiaai-ros-dev
- merged Dockerfiles into a single one
- added kaiaai_python package
- paused building/releasing kaia-ros image
  - use kaia-ros-dev instead of kaia-ros
- merged kaiaai into kaiaai-ros-dev
- kaiaai_cli single main branch

### 2/11/2024
- `docker pull kaiaai/kaiaai-ros-dev:humble-02-11-2024`
- `docker pull kaiaai/kaiaai-ros-dev:iron-02-11-2024`
- [ROS2 kaiaai_telemetry package](https://github.com/kaiaai/kaiaai)
  - added support for 3irobotix Delta-2A, Delta-2G laser distance scan sensors

### 2/5/2024
- `docker pull kaiaai/kaiaai-ros-dev:humble-02-05-2024`
- `docker pull kaiaai/kaiaai-ros-dev:iron-02-05-2024`
- added LiDAR/LDS laser distance scan sensors support
  - YDLIDAR X3, X3-PRO
  - Neato XV11
  - SLAMTEC RPLIDAR A1
- split kaiaai_telemetry config into default and custom
  - `kaiaai/kaiaai_telemetry/config/telem.yaml` is the default config
  - `makerspet_loki/config/telem.yaml` is the custom config for the Loki robot model
  - `makerspet_fido/config/telem.yaml` is the custom config for the Fido robot model
  - `makerspet_snoopy/config/telem.yaml` is the custom config for the Snoopy robot model

### 1/28/2024
- `docker pull kaiaai/kaiaai-ros-dev:humble-01-28-2024`
- `docker pull kaiaai/kaiaai-ros-dev:iron-01-28-2024`
- added YDLIDAR X2 to kaiaai_telemetry
- Arduino firmware moved to https://github.com/kaiaai/firmware

### 1/21/2024
- `docker pull kaiaai/kaiaai-ros-dev:humble-01-21-2024`
- `docker pull kaiaai/kaiaai-ros-dev:iron-01-21-2024`
- kaiaai_telemetry now supports multiple laser distance scan sensor models
  - added Xiaomi 1st gen LDS02RR LDS; YDLIDAR X4 is default
  - updated config/telem.yaml settings in makerspet_loki/fido/snoopy
  - `ros2 launch kaiaai_bringup physical.launch.py robot_model:=makerspet_loki lds_model:=LDS02RR`
  - `ros2 launch kaiaai_bringup physical.launch.py robot_model:=makerspet_loki lds_model:=YDLIDAR-X4`
- Frontier exploration works, but needs debug
  - `ros2 launch explore_lite explore.launch.py`

### 12/11/2023
- `docker pull kaiaai/kaiaai-ros-dev:humble-2023-12-11`
- `docker pull kaiaai/kaiaai-ros-dev:iron-2023-12-11`
- increased map saver timeout
- Nav2 SLAM works in physical robot and in simulation
  - `ros2 launch kaiaai_bringup navigation.launch.py robot_model:=makerspet_loki slam:=True`
- kaiaai_teleop bugfix missing setup file
