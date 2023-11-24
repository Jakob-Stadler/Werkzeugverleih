#!/bin/sh
echo "Creating virtual Python3 environment in ./venv/"
python3 -m venv ./venv
echo "Installing required Python package dependencies"
./venv/bin/pip3 install -r requirements.txt
