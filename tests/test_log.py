"""
name:
  Werkzeugverleih tests
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Collection of tests for werkzeugverleih.log
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import pytest


# ------------------------------------------------------------------------------
@pytest.fixture(scope='module', autouse=True)
def default_statements():
  cfg.LOG_LEVEL = 'debug'
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  cfg.LOG_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_initialize_logger_default():
  log.initialize_logger()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_initialize_logger_debug():
  log.initialize_logger(level='debug')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_initialize_logger_malformed():
  log.initialize_logger(level='some_data')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_change_log_file_arg():
  log.initialize_logger()
  log.change_log_file('tests/scratch/file.log')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_log_debug():
  log.initialize_logger()
  log.log('test', level='debug')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_log_malformed():
  log.initialize_logger()
  log.log('test', level='some_data')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def mock_daychange():
  original_today = log.today
  original_change_log_file = log.change_log_file

  from datetime import date, timedelta
  saved_date = date.today()

  def mock_today_function():
    '''every call advances the date by one day'''
    nonlocal saved_date
    saved_date += timedelta(days=1)
    return saved_date

  log.today = mock_today_function

  log_file_changed = False

  def mock_change_log_file(filename=None):
    nonlocal log_file_changed
    log_file_changed = True

  log.change_log_file = mock_change_log_file

  def get_log_file_changed():
    nonlocal log_file_changed
    return log_file_changed

  yield get_log_file_changed

  log.change_log_file = original_change_log_file
  log.today = original_today
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_log_daychange(mock_daychange):
  log.initialize_logger()
  log.log('test', level='info')
  log.log('test', level='info')
  assert mock_daychange()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_log_file():
  log.initialize_logger()
  f = log.current_log_file()
  assert f is not None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_log_file_no_handler():
  import logging
  log.logger = logging.getLogger(name='werkzeugverleih')
  for handler in log.logger.handlers:
    log.logger.removeHandler(handler)

  n = log.current_log_file()
  assert n is None
# ------------------------------------------------------------------------------
