#!/bin/sh

PYTHONWARNINGS="ignore" coverage run --source=.,src,node -m unittest discover -s src/
PYTHONWARNINGS="ignore" coverage run --source=.,src,node -m unittest discover -s node/
coverage combine
coverage report
coveralls

docker-compose build
docker-compose up -d
sleep 20s
docker-compose logs
bash ./discord/run_tests.sh
docker-compose stop
docker-compose rm -f

#podman-compose up -d
#sleep 20s
#podman-compose logs discord
#bash ./src/run_tests.sh
#podman-compose stop discord node web