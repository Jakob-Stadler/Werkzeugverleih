# Werkzeugverleih

#### Disclaimer

This project was originally a student project made by Jakob Stadler and
Matthias Sagmeister and was hosted on an internal Gitlab instance,
it has been cleared of any internal/copyrighted data and made
publically available here. Some comments/documentation may not appy anymore.

## About this project

This repository houses the "backend" application for a self-service kiosk "web
app" for a tool/machine storage rental system. It is designed to run locally
on a Raspberry Pi based hardware plattform with no active Internet connection.
More on hardware below.

The software is primarily written in Python3 and heavily relies on the
[Flask micro web application framework](https://flask.palletsprojects.com/) to
build and serve a locally-hosted website with the intention of having a simple
web browser in kiosk mode play the role of graphical frontend application.

In that sense, it's not only the backend, since it also contains all the
html-templates/css/js that make up the core of the app frontend.



## Usage

Once the installation and configuration steps are completed, the application
can be started either with the shell script `./run.sh` (for debugging on
Windows: `.\run.bat` ) or by manually following these steps:

1. Activate virtual environment `source ./venv/bin/activate`
(for debugging on Windows: `.\venv\Scripts\activate` )
2. Start Application `python3 ./start_werkzeugverleih.py`

Finally:
* Start Browser (chromium) and point to address http://127.0.0.1:5000/index



## Installation

0. Required dependency: Python 3.8 (Through your package manager or by
[downloading the binaries from python.org](https://www.python.org/downloads/))
1. git clone / download and extract this repository
+ `git clone https://mygit.th-deg.de/mk4_werkzeugverleih/werkzeugverleih_backend.git`
+ `cd ./werkzeugverleih_backend/`

From here on out, there's a shell script to make installation easier.
Simply run `./install.sh` (for debugging on Windows: `install.bat` )
or alternatively, follow these steps:

2. `python3 -m venv ./venv`  (for debugging on Windows: `py -3 -m venv ./venv`,
Python Launcher required)
3. `source ./venv/bin/activate`  (for debugging on Windows: `.\venv\Scripts\activate` )
4. `pip3 install -r requirements.txt`



## Configuration

All configurable Python variables are exposed to non-hardcoded changes in
`data/werkzeugverleih.json`.

See [CONFIGURATION.md](CONFIGURATION.md)



## Testing

Before pushing changes to the repository, be sure to run the testing
procedures locally first.

1. For static code style analysis, run: `flake8`
2. For testing and code coverage, run: `./test.sh` (for debugging on Windows
`test.bat` )

**Local testing preempts bad surpises!** \
Gitlab will run both jobs in its Continous Integration routine and fail
new commits that don't pass tests. Be smart, run them locally first, and
fix any occurences before embarassing yourself on the project CI pipeline.



## Hardware

* Raspberry Pi 4 Model B 4GB
* Raspberry Cam V2
* Tinkerforge NFC Bricklet
* 15.6" FullHD Touchdisplay