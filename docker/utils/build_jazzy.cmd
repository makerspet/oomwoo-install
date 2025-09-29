docker login
cd .\kaiaai_jazzy
docker image rm kaiaai/kaiaai:jazzy
docker build --no-cache -t kaiaai/kaiaai:jazzy .
docker push kaiaai/kaiaai:jazzy
cd ..
