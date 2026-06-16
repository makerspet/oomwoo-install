docker login
docker image rm makerspet/oomwoo:jazzy
docker system prune -f -a
docker buildx create --name kaiaai --driver=docker-container
cd .\kaiaai
docker buildx build --builder=kaiaai --no-cache --provenance=true -t makerspet/oomwoo:jazzy --push --load .
docker rm buildx_buildkit_kaiaai0 --force