#!/bin/sh

docker-compose build

docker run --mount src=$(pwd)/node/,target=$(pwd)/node,type=bind -w="$(pwd)/node" geiler-musik-bot_node sh -c "pip install coverage && PYTHONWARNINGS='ignore' coverage run --parallel-mode --source=. -m unittest discover"
mv ./node/.coverage* ./.coverage.node
docker run --mount src=$(pwd),target=$(pwd),type=bind --env-file=sysenv.env -w="$(pwd)" geiler-musik-bot_discord sh -c "pip install coverage && PYTHONWARNINGS='ignore' coverage run --source=.,src -m unittest discover -s src/"
coverage combine
coverage report
coveralls

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