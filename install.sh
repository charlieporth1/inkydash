#!/bin/bash

apt update
apt install -y python3
apt install -y python3-dev
apt install -y python3-pip
apt install -y python3-bs4
apt install -y python3-numpy
apt install -y python3-pandas
apt install -y python3-wheel
apt install -y python3-setuptools
apt install -y libcurl4-openssl-dev
apt install -y 2to3
apt install -y libgcc-s1 libstdc++6 libc6 python3-dev build-essential libssl-dev
apt install -y libffi-dev

SCRIPT_DIR=`realpath .`

pip install --upgrade pip wheel setuptools --break-system-packages
pip install -r $SCRIPT_DIR/requirements.txt --break-system-packages

cp -rfv libcurl* /lib/arm-linux-gnueabihf/
rm -rfv /usr/lib/python3/dist-packages/beautifulsoup4-4.13.4.dist-info
ln -s /usr/lib/python3/dist-packages/bs4  /usr/lib/python3/dist-packages/beautifulsoup4-4.13.4.dist-info

cp -rfv *.so* /usr/lib/python3/dist-packages/beautifulsoup*/
cp -rfv *.so* /usr/lib/python3/dist-packages/bs4*/
cp -rfv *.so* /usr/lib/python3/dist-packages/

cp -rf $SCRIPT_DIR/fonts /usr/share/fonts/truetype/
cp -rf $SCRIPT_DIR/einky.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable einky.service
sudo systemctl start einky.service
