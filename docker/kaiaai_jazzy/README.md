This Docker file builds the [Kaia.ai](https://kaia.ai/) robot software platform image.

Please find the description, setup and operation details [here](https://github.com/kaiaai/kaiaai).

A pre-built Docker image is available at [Docker Hub](https://hub.docker.com/r/kaiaai/kaiaai)

## Re-building the Docker image
If you would like to modify and/or rebuild this image:
- change your current directory in your shell to the location of this Docker file
- optionally, edit the Dockerfile as you wish
- run the command below to build the Docker image using ROS2 `iron` release:

```
docker build --no-cache -t kaiaai/kaiaai:iron --build-arg distro_tag=iron .
```
