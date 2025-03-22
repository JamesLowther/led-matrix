#!/bin/bash

OLD_PWD=$(pwd)
cd $(dirname $0)

sudo python3 ./src/main.py --led-slowdown-gpio 2 --led-brightness 85 --led-drop-privs-user dietpi --led-drop-privs-group gpio

cd $OLD_PWD
