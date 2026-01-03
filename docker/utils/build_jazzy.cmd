docker login
cd .\kaiaai
docker image rm kaiaai/kaiaai:jazzy
docker build --no-cache -t kaiaai/kaiaai:jazzy .
cd ..
