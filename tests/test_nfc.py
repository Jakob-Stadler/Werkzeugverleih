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
  Collection of tests for werkzeugverleih.main
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import werkzeugverleih.nfc as nfc
import pytest


file_contents = ''
with open('./tests/res/nfc.txt', 'r') as nfc_file:
  file_contents = nfc_file.read()


# ------------------------------------------------------------------------------
@pytest.fixture(scope='module', autouse=True)
def default_statements():
  cfg.LOG_LEVEL = 'debug'
  cfg.NFC_DEBUG_DELAY = 0
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  cfg.LOG_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'

  log.initialize_logger()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def restore_nfc_file():
  with open('./tests/res/nfc.txt', 'w') as nfc_file:
    nfc_file.write(file_contents)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_tag_id_debug():
  cfg.DEBUG = True
  with open('./tests/res/nfc.txt', 'w') as nfc_file:
    nfc_file.write('NFC_ID')
    nfc_id = 'NFC_ID'
  n = nfc.get_tag_id()
  restore_nfc_file()
  assert n == nfc_id
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_tag_id_debug_None():
  cfg.DEBUG = True
  with open('./tests/res/nfc.txt', 'w') as nfc_file:
    nfc_file.write('')

  n = nfc.get_tag_id()

  restore_nfc_file()

  assert n is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_tag_id_prod():
  cfg.DEBUG = False
  n = nfc.get_tag_id()
  assert n is None
# ------------------------------------------------------------------------------
