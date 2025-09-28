docker login
cd .\kaiaai
docker image rm kaiaai/kaiaai-dev:iron
docker build --no-cache -t kaiaai/kaiaai-dev:iron --build-arg distro_tag=iron .
docker push kaiaai/kaiaai-dev:iron
cd ..
