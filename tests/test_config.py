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
  Collection of tests for werkzeugverleih.config
dependencies:
  pytest
"""

import werkzeugverleih.config as config
from os.path import abspath

DEFAULT_CONFIG = abspath('tests/res/default_config.json')
EMPTY_CONFIG = abspath('tests/res/empty_config.json')
MALFORMED_CONFIG = abspath('tests/res/malformed_config.json')
IRRELEVANT_CONFIG = abspath('tests/res/irrelevant_config.json')


# ------------------------------------------------------------------------------
def test_load_default_config():
  config.STREAM_FRAMERATE = None
  config.load_config(DEFAULT_CONFIG)
  assert config.STREAM_FRAMERATE == 4
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_load_empty_config():
  config.STREAM_FRAMERATE = None
  config.load_config(EMPTY_CONFIG)
  assert config.STREAM_FRAMERATE is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_load_malformed_config():
  config.STREAM_FRAMERATE = None
  config.load_config(MALFORMED_CONFIG)
  assert config.STREAM_FRAMERATE is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_load_irrelevant_config():
  config.STREAM_FRAMERATE = None
  config.load_config(IRRELEVANT_CONFIG)
  assert config.STREAM_FRAMERATE is None
# ------------------------------------------------------------------------------
