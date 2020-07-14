#!/bin/sh

docker-compose build

docker run \
    --mount src=$(pwd)/node/,target=$(pwd)/node,type=bind \
    -w="$(pwd)/node" \
    geiler-musik-bot_node \
    sh -c "pip install coverage && PYTHONWARNINGS='ignore' coverage run --omit='*discord_tests*' --parallel-mode --source=. -m unittest discover"

docker run \
    --mount src=$(pwd),target=$(pwd),type=bind \
    --env-file=sysenv.env -w="$(pwd)" \
    geiler-musik-bot_discord \
    sh -c "pip install coverage && PYTHONWARNINGS='ignore' coverage run --omit='*discord_tests*' --parallel-mode --source=.,src -m unittest discover -s src/"


docker run \
    --mount src=$(pwd),target=$(pwd),type=bind \
    --env-file=sysenv.env -w="$(pwd)" \
    --network="web" \
    --rm \
    --name discord \
    geiler-musik-bot_discord \
    sh -c "pip install coverage && coverage run --source=.,src --parallel-mode --omit='*discord_tests*' src/discord_main.py" \
    &

docker run \
    --mount src=$(pwd)/node/,target=$(pwd)/node,type=bind \
    -w="$(pwd)/node" \
    --network="web" \
    --rm \
    geiler-musik-bot_node \
    sh -c "pip install coverage && /wait.sh -t 0 discord:9988 -- coverage run --omit='*discord_tests*' --source=. --parallel-mode node.py" \
    &

sleep 30s
bash ./src/run_tests.sh
docker container wait discord

mv ./node/.coverage* .

coverage combine
coverage report
coveralls

#podman-compose up -d
#sleep 20s
#podman-compose logs discord
#bash ./src/run_tests.sh
#podman-compose stop discord node web