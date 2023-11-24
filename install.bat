@echo off
echo Creating virtual Python3 environment in ./venv/
py -3 -m venv ./venv
echo Installing required Python package dependencies
./venv/Scripts/pip3 install -r requirements.txt
