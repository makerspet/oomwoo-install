cd .\kaiaai
docker buildx build --builder=kaiaai --no-cache --provenance=true -t makerspet/oomwoo:jazzy-dev --push --load .
docker rm buildx_buildkit_kaiaai0 --force