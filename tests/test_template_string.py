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
  Collection of tests for werkzeugverleih.template_string
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.template_string as template_string


# ------------------------------------------------------------------------------
def test_log_filename():
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  s = template_string.log_filename('1234-56-78')
  assert s == 'log_1234-56-78.log'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_log_filepath():
  cfg.LOG_FILEPATH_TEMPLATE = 'data/logs/${filename}'
  s = template_string.log_filepath('filename.ext')
  assert s == 'data/logs/filename.ext'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_backup_filename():
  cfg.BACKUP_FILENAME_TEMPLATE = 'backup_${date}.db'
  s = template_string.backup_filename('1234-56-78')
  assert s == 'backup_1234-56-78.db'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_backup_filepath():
  cfg.BACKUP_FILEPATH_TEMPLATE = 'data/db_backups/${filename}'
  s = template_string.backup_filepath('filename.ext')
  assert s == 'data/db_backups/filename.ext'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_user():
  user = {'nfc_id': '012345678',
          'given_name': 'GIVEN',
          'surname': 'SUR',
          'room': 'ROOM' }
  cfg.CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'
  s = template_string.current_user(user)
  assert s == 'GIVEN SUR, ROOM'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_user_malformed_dict():
  user = {'some_key': 'some_data'}
  cfg.CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'
  s = template_string.current_user(user)
  assert s == ' , '
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_user_malformed_data():
  user = ['data1', 'data2']
  cfg.CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'
  s = template_string.current_user(user)
  assert s == ''
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_current_user_None():
  user = None
  cfg.CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'
  s = template_string.current_user(user)
  assert s == ''
# ------------------------------------------------------------------------------
