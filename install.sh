#!/bin/bash

SCRIPT_DIR=`realpath .`
cp -rf $SCRIPT_DIR/fonts /usr/share/fonts/truetype/
cp -rf $SCRIPT_DIR/einky.service /etc/systemd/system/
pip3 install -r $SCRIPT_DIR/requirements.txt
sudo systemctl daemon-reload
sudo systemctl enable einky.service
sudo systemctl start einky.service
