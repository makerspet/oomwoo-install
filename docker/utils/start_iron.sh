#!/bin/bash

xhost local:root
XAUTH=/tmp/.docker.xauth

sudo docker run -it \
  --name=makerspet \
  --rm \
  -p 8888:8888/udp \
  -p 4430:4430/tcp \
  --env="DISPLAY=$DISPLAY" \
  --env="QT_X11_NO_MITSHM=1" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --env="XAUTHORITY=$XAUTH" \
  --volume="$XAUTH:$XAUTH" \
  --net=host \
  --privileged \
  kaiaai/kaiaai:iron

  echo "Done"