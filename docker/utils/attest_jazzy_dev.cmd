docker login
docker image rm kaiaai/kaiaai:jazzy-dev
docker system prune -f -a
docker buildx create --name kaiaai --driver=docker-container
cd .\kaiaai
docker buildx build --builder=kaiaai --no-cache --provenance=true -t kaiaai/kaiaai:jazzy-dev --push --load .
docker rm buildx_buildkit_kaiaai0 --force
# docker pull kaiaai/kaiaai:jazzy-dev