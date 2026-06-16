#!/bin/bash

xhost local:root
XAUTH=/tmp/.docker.xauth

sudo docker run -it \
  --name=makerspet \
  --rm \
  -p 8888:8888/udp \
  --env="DISPLAY=$DISPLAY" \
  --env="QT_X11_NO_MITSHM=1" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --env="XAUTHORITY=$XAUTH" \
  --volume="$XAUTH:$XAUTH" \
  --net=host \
  --privileged \
  --add-host="host.docker.internal:host-gateway" \
  makerspet/oomwoo:jazzy

  echo "Done"