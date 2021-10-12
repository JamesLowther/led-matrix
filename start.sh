#!/bin/bash

OLD_PWD=$(pwd)
cd $(dirname $0)

git pull
sudo python3 ./src/main.py

cd $OLD_PWD
