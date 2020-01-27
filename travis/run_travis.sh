#!/bin/sh
pytest discord/test.py
coveralls
docker-compose build
docker-compose up -d
sleep 20s
docker-compose logs
bash ./discord/run_tests.sh
docker-compose stop
docker-compose rm -f
podman-compose up -d
sleep 20s
podman-compose logs discord
bash ./discord/run_tests.sh
podman-compose stop discord parent node web

# create node executable
cd youtube/node/ || exit
cp node.py node.pyx
cython node.pyx --embed -3
gcc -Os -I /usr/include/python3.7m -o node node.c -lpython3.7m -lpthread -lm -lutil -ldl
