#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
set -e

echo "Starting Node Bootstrap..."

sudo apt-get update -y
sudo apt-get install -y git python3-pip python3-dev libpcap-dev tcpdump

echo "Installing Python dependencies..."
sudo pip3 install --no-cache-dir \
    scapy \
    pandas \
    numpy \
    pyyaml 

sudo pip3 install git+https://github.com/meeron/pybinn.git

# config for scapy
sudo setcap cap_net_raw,cap_net_admin=eip $(readlink -f $(which python3))

echo "Bootstrap Complete."