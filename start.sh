#!/bin/bash

OLD_PWD=$(pwd)
cd $(dirname $0)

git pull
sudo python3 ./src/main.py --led-gpio-mapping=adafruit-hat-pwm

cd $OLD_PWD
