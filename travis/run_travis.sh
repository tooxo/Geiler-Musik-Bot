#!/bin/sh

PYTHONWARNINGS="ignore" coverage run --source=.,discord -m unittest discover -s discord/ && coverage report
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
#bash ./discord/run_tests.sh
#podman-compose stop discord node web