cd .\kaiaai
docker buildx build --builder=kaiaai --no-cache --provenance=true -t kaiaai/kaiaai:jazzy-dev --push --load .
docker rm buildx_buildkit_kaiaai0 --force
docker pull kaiaai/kaiaai:jazzy-dev