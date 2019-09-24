#!/bin/bash

pip install distest
cd discord || exit
python3 discord_tests.py "$TARGET_NAME" "$TESTER_TOKEN" --channel "$CHANNEL" --run all