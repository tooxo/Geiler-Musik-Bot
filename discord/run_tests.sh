#!/bin/bash

# sudo apt install libopus0
# git clone https://github.com/tooxo/distest.git --depth 1 -b test
# cd distest || exit 1
# pip3 install -r requirements-dev.txt
# pip3 install .
# cd ./../discord || exit 1
# pip3 install pynacl
cd ./discord || exit 1
python3 -u discord_tests.py "$TARGET_NAME" "$TESTER_TOKEN" --channel "$CHANNEL" --run all || :
