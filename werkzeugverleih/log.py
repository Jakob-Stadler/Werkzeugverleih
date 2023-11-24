"""
name:
  Werkzeugverleih Logging
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Interface between other modules and logging provider.
dependencies:
  -
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
from werkzeugverleih.template_string import log_filename, log_filepath
# ------------------------------------------------------------------------------


# HELPER FUNCTIONS =============================================================
from datetime import date
def today():
  return date.today()
# ==============================================================================


# LOGGING FUNCTIONS ============================================================
import logging
logger = None
log_date = today()
# ------------------------------------------------------------------------------
def initialize_logger(level: str = 'info') -> None:
  '''start the logger with default settings'''
  global logger
  if logger is None:
    logger = logging.getLogger(name='werkzeugverleih')
    change_log_file(filename=None)

  map_level = { 'debug':    logging.DEBUG,
                'info':     logging.INFO,
                'warning':  logging.WARNING,
                'error':    logging.ERROR,
                'critical': logging.CRITICAL}

  if level in map_level:
    logger.setLevel(map_level.get(level, logging.INFO))
  else:
    logger.setLevel(logging.INFO)

  log(f'log.initialize_logger(): ready to start logging with level "{level}"',
      level='info')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from datetime import datetime as dt
from time import gmtime
def change_log_file(filename: str = None) -> None:
  '''change the log destination of the active logger

  arguments:
  + `filename` - string, path of the file to be written to

  if filename=None, will default to the filename set by template
  cfg.LOG_FILEPATH_TEMPLATE, cfg.LOG_FILENAME_TEMPLATE, and cfg.DATE_FORMAT
  '''
  global logger

  if filename is None:
    filename = log_filepath(log_filename(dt.now().strftime(cfg.DATE_FORMAT)))

  file_handler = logging.FileHandler(filename=filename, mode='a',
                                      encoding='utf-8')

  formatter = logging.Formatter(fmt=cfg.LOGGING_FORMAT,
                                datefmt=cfg.LOGGING_DATETIME_FORMAT)
  formatter.converter = gmtime
  file_handler.setFormatter(formatter)

  for handler in logger.handlers:
    logger.removeHandler(handler)

  logger.addHandler(file_handler)

  global log_date
  log_date = today()

  # Don't log this message, since it's guaranteed to appear in the new file,
  # which already knows it's own filename
  print(f' - Changing log file to file "{filename}"')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def log(message: str = '', level: str = 'info') -> None:
  '''logs `message` in currently set logfile

  arguments:
  + `message` - string, text to save in logfile
  + `level` - string, plaintext log level

  valid values for levels include [`debug`, `info`, `warning`, `error`,
  `critical`], will default to `info`
  '''
  global logger

  # change log file when date changes
  if log_date != today():
    change_log_file()

  map_f = { 'debug':    logger.debug,
            'info':     logger.info,
            'warning':  logger.warning,
            'error':    logger.warning,
            'critical': logger.critical }

  if level in map_f:
    log_f = map_f.get(level, logger.info)
  else:
    log_f = logger.info

  log_f(message)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def current_log_file() -> str:
  '''returns the filename of the active logger's first filehandler'''
  filenames = [i.baseFilename for i in logger.handlers
                if hasattr(i, 'baseFilename')]
  if filenames:
    return filenames[0]

  return None
# ------------------------------------------------------------------------------
# ==============================================================================
