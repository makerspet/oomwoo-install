docker login
docker image rm kaiaai/kaiaai:jazzy
docker system prune -f -a
docker buildx create --name kaiaai --driver=docker-container
cd .\kaiaai
docker buildx build --builder=kaiaai --no-cache --provenance=true -t kaiaai/kaiaai:jazzy --push --load .
docker rm buildx_buildkit_kaiaai0 --force