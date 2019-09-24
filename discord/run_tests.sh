#!/bin/bash

git clone https://github.com/tooxo/distest.git --depth 1
cd distest
pip3 install -r requirements-dev.txt
pip3 install .
cd ./../discord
pip3 install -r requirements.txt
python3 -u discord_tests.py "$TARGET_NAME" "$TESTER_TOKEN" --channel "$CHANNEL" --run all
