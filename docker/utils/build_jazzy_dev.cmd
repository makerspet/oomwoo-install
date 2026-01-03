docker login
cd .\kaiaai
docker image rm kaiaai/kaiaai:jazzy-dev
docker build --no-cache -t kaiaai/kaiaai:jazzy-dev .
docker push kaiaai/kaiaai:jazzy-dev
cd ..
