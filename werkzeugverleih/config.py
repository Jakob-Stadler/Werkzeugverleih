"""
name:
  Werkzeugverleih Configuration Management
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Provides a set of default values for other modules and allows
  to optionally override them via json files.
dependencies:
  -
"""


# ------------------------------------------------------------------------------
# Default Settings, will get overwritten by load_config()
DEBUG = False
LOG_LEVEL = 'info'

UI_DEFAULT_LANGUAGE = 'en'

NFC_DEBUG_DELAY = 2  # in seconds

STREAM_FRAMERATE = 30  # in Hz
KEEP_BACKUPS_FOR_X_DAYS = 2
KEEP_LOGS_FOR_X_DAYS = 14

INACTIVITY_LIMIT_DAYS = 180

FLASK_CONFIG_LOCATION = 'data/flask.cfg'
DATABASE_FILE_LOCATION = 'data/werkzeugverleih.db'

LOG_FILENAME_TEMPLATE = 'log_${date}.log'
LOG_FILEPATH_TEMPLATE = 'data/logs/${filename}'
BACKUP_FILENAME_TEMPLATE = 'backup_${date}.db'
BACKUP_FILEPATH_TEMPLATE = 'data/db_backups/${filename}'

CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
LOGGING_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'

LOGGING_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'

NFC_CACHE_DURATION = 5  # seconds
NFC_SCAN_TIMEOUT = 3  # seconds
NFC_POLL_INTERVALL = 0.1  # seconds
NFC_BRICKLET_UID = "PMv"  # Individual UID of NFC-Bricklet
BRICKD_HOST = "localhost"  # standard Host for running programm on raspberry PI
BRICKD_PORT = 4223  # standard port for running programm on raspberry PI
NFC_SEARCH_INTERVALL = 1  # intervall for searching for NFC-Chip

CAMERA_TIMEOUT = 10  # seconds until camera shutdown if it's not needed anymore

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
config_file = 'data/werkzeugverleih.json'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# filter global variables by upper case first letter
_config_variables_ = [v for v in dir() if v[:1].isupper()]

from json import load as json_load
from json import JSONDecodeError
def load_config(json_file: str) -> None:
  '''parse a json file and store settings for matching global variables'''
  with open(json_file) as config_file:
    try:
      config_data = json_load(config_file)
    except JSONDecodeError:
      # logging not yet initialized, print only
      print('[!]ERROR[!] config.load_config():\n'
            '    JSON decoding error while trying to load '
            f'file "{config_file}"\n'
            'Application will continue with prior (default) config.')
      return

    for key in config_data:
      if key in _config_variables_:
        globals()[key] = config_data[key]
# ------------------------------------------------------------------------------
