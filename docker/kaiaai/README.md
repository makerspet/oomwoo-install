A pre-built Docker image is available at [Docker Hub](https://hub.docker.com/r/makerspet/oomwoo)

## Re-building the Docker image
If you would like to modify and/or rebuild this image:
- change your current directory in your shell to the location of this Docker file
- optionally, edit the Dockerfile as you wish

```
docker build --no-cache -t makerspet/oomwoo:jazzy-dev .
```