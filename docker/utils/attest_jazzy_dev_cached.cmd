docker login
docker image rm makerspet/oomwoo:jazzy-dev
docker buildx create --name kaiaai --driver=docker-container
cd .\kaiaai
docker buildx build --builder=kaiaai --provenance=true -t makerspet/oomwoo:jazzy-dev --push --load .
docker rm buildx_buildkit_kaiaai0 --force