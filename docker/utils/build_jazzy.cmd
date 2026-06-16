docker login
cd .\kaiaai
docker image rm makerspet/oomwoo:jazzy
docker build --no-cache -t makerspet/oomwoo:jazzy .
cd ..
