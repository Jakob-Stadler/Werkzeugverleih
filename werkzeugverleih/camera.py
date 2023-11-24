"""
name:
  Werkzeugverleih Camera Management
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Provides image data for the rental system.
dependencies:
  picamera
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
# ------------------------------------------------------------------------------
import time
import io
try:
  import picamera
except (ModuleNotFoundError, FileNotFoundError):
  cfg.DEBUG = True
from threading import Thread

thread = None
frames = None
camera_frame = None
last_access = 0

# ------------------------------------------------------------------------------
def initialize_camera():
  '''public interface
  prerequisites before being able to capture images'''

  global thread, frames

  if cfg.DEBUG:
    frames = [open(f'tests/res/{f}.jpg', 'rb').read() for f in ['1', '2', '3']]
  else:
    if thread is None:
        thread = Thread(target=get_camera_frame)
        thread.start()
        while camera_frame is None:
            time.sleep(0.1)

# ------------------------------------------------------------------------------

def get_jpeg():
  '''public interface

  get image data (1920x1080 jpeg) as binary string
  '''
  global camera_frame, frames, last_access

  if time.time() - last_access > cfg.CAMERA_TIMEOUT:
    initialize_camera()

  last_access = time.time()
  # DEBUG
  if cfg.DEBUG:
    return frames[int(time.time() * cfg.STREAM_FRAMERATE) % 3]
  else:
    return camera_frame

  # DEFAULT -> None (let caller deal with it)
  return None

# ------------------------------------------------------------------------------

def get_camera_frame():
  global thread, camera_frame, last_access
  with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080)
    camera.hflip = True  # flips camera horizontally
    camera.vflip = True  # flips camera vertically

    stream = io.BytesIO()
    for foo in camera.capture_continuous(stream, 'jpeg',
                                          use_video_port=True):
      stream.seek(0)
      camera_frame = stream.read()

      stream.seek(0)
      stream.truncate()

      if time.time() - last_access > cfg.CAMERA_TIMEOUT:
        break
  thread = None

  # DEFAULT -> None (let caller deal with it)
  return None
# ------------------------------------------------------------------------------


# see https://github.com/miguelgrinberg/flask-video-streaming
# especially the older and simpler verion
# https://github.com/miguelgrinberg/flask-video-streaming/tree/v1
