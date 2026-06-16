docker login
cd .\kaiaai
docker image rm makerspet/oomwoo:jazzy-dev
docker build --no-cache -t makerspet/oomwoo:jazzy-dev .
cd ..
