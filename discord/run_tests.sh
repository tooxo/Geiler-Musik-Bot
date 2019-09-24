#!/bin/bash

git clone https://github.com/tooxo/distest.git --depth 1
cd distest
pip install -r requirements-dev.txt
pip install .
cd ./../discord
python3 -u discord_tests.py "$TARGET_NAME" "$TESTER_TOKEN" --channel "$CHANNEL" --run all
