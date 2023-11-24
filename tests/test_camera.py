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
  Collection of tests for werkzeugverleih.camera
dependencies:
  pytest
  PIL
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.camera as camera
from io import BytesIO
from PIL import Image
import pytest


# ------------------------------------------------------------------------------
@pytest.fixture(scope='module', autouse=True)
def default_statements():
  cfg.DEBUG = True
  cfg.STREAM_FRAMERATE = 1000
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_debug_get_jpeg():
  cfg.DEBUG = True
  camera.initialize_camera()

  jpeg_bytes = camera.get_jpeg()

  stream = BytesIO(jpeg_bytes)

  with Image.open(stream) as image:
    image.verify()

    assert image.format == 'JPEG'

    width, height = image.size

    assert width == 1920
    assert height == 1080
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_prod_get_jpeg():
  cfg.DEBUG = False
  camera.initialize_camera()
  ''' # temporarily disabled until fully implemented
  jpeg_bytes = camera.get_jpeg()

  stream = BytesIO(jpeg_bytes)

  with Image.open(stream) as image:
    image.verify()

    assert image.format == 'JPEG'

    width, height = image.size

    assert width == 1920
    assert height == 1080
  '''
  # Remove this line when uncommenting the block above
  camera.get_jpeg()
# ------------------------------------------------------------------------------
