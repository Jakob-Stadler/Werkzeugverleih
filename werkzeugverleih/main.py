"""
name:
  Werkzeugverleih Main Entry Point
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Main entry point for package, call main() to start application.
dependencies:
  -
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import werkzeugverleih.nfc as nfc
import werkzeugverleih.database as db
import werkzeugverleih.webserver as webserver
import werkzeugverleih.routine as routine
# ------------------------------------------------------------------------------


# shared imports ---------------------------------------------------------------
from sys import exit
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from os.path import exists
from os import urandom
def default_flask_config_if_missing() -> None:
  '''create default Flask config if no config file exists yet'''
  if not exists(cfg.FLASK_CONFIG_LOCATION):
    try:
      with open(cfg.FLASK_CONFIG_LOCATION, 'w') as flask_cfg:
        flask_cfg.write('SECRET_KEY = ' + str(urandom(32)))
        log.log('main.default_flask_config_if_missing(): wrote file '
                f'"{cfg.FLASK_CONFIG_LOCATION}"', level='info')
    except FileNotFoundError:
      print(f'ERROR: Failed to create "{cfg.FLASK_CONFIG_LOCATION}"')
      print('Did you modify the default directory structure?')
      log.log('main.default_flask_config_if_missing(): failed to create '
              f'"{cfg.FLASK_CONFIG_LOCATION}"', level='criticial')
      exit(1)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def main() -> None:
  '''program entry point'''
  # load configuration from json file
  if exists(cfg.config_file):
    cfg.load_config(json_file=cfg.config_file)
    print('++ Loading configuration data from '
          f'json file: "{cfg.config_file}" ++')

  log.initialize_logger(cfg.LOG_LEVEL)
  print(f'++ Starting logging in file "{log.current_log_file()}" ++')
  log.log('main(): starting up main program', level='info')

  # create default Flask config if no config file exists yet
  default_flask_config_if_missing()

  log.log('main(): initializing database', level='info')
  db.initialize_connection()
  db.create_tables()

  log.log('main(): initializing nfc', level='info')
  nfc.initialize_nfc()

  log.log('main(): starting routine operation thread', level='info')
  routine.start_routine()

  log.log('main(): starting webserver', level='info')
  webserver.start_webserver()

  print('Shutting down application')

  log.log('main(): shutting down program', level='info')
  routine.stop_routine()
  db.close_connection()
  nfc.stop_nfc()
  log.log('main(): all modules finished, exit now', level='info')
  exit(0)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
if __name__ == '__main__':
  main()
# ------------------------------------------------------------------------------
