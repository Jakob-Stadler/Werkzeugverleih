"""
name:
  Werkzeugverleih NFC Authentication
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Interface between other modules and NFC reader hardware.
  In theory, the application can use other means of authentication, like
  biometrics or other hardware tokens, as long as get_tag_id() provides
  one unique ID per user.
dependencies:
  tinkerforge
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
from werkzeugverleih.log import log
import werkzeugverleih.camera as cam
import werkzeugverleih.display as display
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from time import time, sleep
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc import BrickletNFC
cached_id = None
cached_timestamp = 0
def cb_reader_state_changed(state, idle, nfc):
    global cached_id, cached_timestamp
    if state == nfc.READER_STATE_IDLE:
        nfc.reader_request_tag_id()
    elif state == nfc.READER_STATE_REQUEST_TAG_ID_READY:
        ret = nfc.reader_get_tag_id()
        cached_id = "".join(s[2:].upper() for s in map(hex, ret.tag_id))
        cached_timestamp = time()
        cam.initialize_camera()
        display.wake_up_screen_via_NFC()
        while cached_timestamp > (time() - cfg.NFC_CACHE_DURATION):
            sleep(.1)
        cached_id = None
        cached_timestamp = 0
        nfc.reader_request_tag_id()
    elif state == nfc.READER_STATE_REQUEST_TAG_ID_ERROR:
      sleep(cfg.NFC_SEARCH_INTERVALL)
      nfc.reader_request_tag_id()

# ------------------------------------------------------------------------------

def initialize_nfc():
  if cfg.DEBUG:
    return
  global cached_id, cached_timestamp, ipcon, stop
  cached_timestamp = 0
  cached_id = None
  stop = False

  ipcon = IPConnection()
  nfc = BrickletNFC(cfg.NFC_BRICKLET_UID, ipcon)
  ipcon.connect(cfg.BRICKD_HOST, cfg.BRICKD_PORT)
  nfc.register_callback(nfc.CALLBACK_READER_STATE_CHANGED,
                          lambda x, y: cb_reader_state_changed(x, y, nfc))
  nfc.set_mode(nfc.MODE_READER)
# ------------------------------------------------------------------------------

def stop_nfc():
  if cfg.DEBUG:
    return
  global cached_id, cached_timestamp, ipcon
  cached_id = None
  cached_timestamp = 0
  ipcon.disconnect()
# ------------------------------------------------------------------------------

def get_tag_id():
  '''public interface
  read NFC tag and return its ID (Hex String)
  return None if no nfc tag after timeout'''
  global cached_id, cached_timestamp

  # DEBUG
  if cfg.DEBUG:
    sleep(cfg.NFC_DEBUG_DELAY)  # fake nfc scan delay
    with open('./tests/res/nfc.txt', 'r') as nfc_file:
      nfc_id = nfc_file.readline()
      if nfc_id == '':
        return None
      print('nfc.get_tag_id(): DEBUG ID: {nfc_id}')
      return nfc_id
  else:
    if cached_timestamp > (time() - cfg.NFC_CACHE_DURATION):
      return cached_id
    else:
      cached_id = None
      cached_timestamp = 0
      for i in range(int(cfg.NFC_SCAN_TIMEOUT / cfg.NFC_POLL_INTERVALL)):
        if cached_timestamp > (time() - cfg.NFC_CACHE_DURATION):
          return cached_id
          sleep(cfg.NFC_POLL_INTERVALL)
  return None
  # ------------------------------------------------------------------------------

  log('nfc.get_tag_id(): No NFC ID available', level='debug')
  return None
# ------------------------------------------------------------------------------

# a viable strategy for a real NFC reader implementation may be running its own
# thread and keeping track of its current state.
# registering a callback to CALLBACK_READER_STATE_CHANGED may do most of the
# legwork.
# the callback should always wake up the screen after inactivity (see display),
# activate the pi camera (see camera) and then try to read the tag id.
# After the tag id has been read, it should be cached for faster responses by
# other parts of the application (most notibly, the webserver)
# Once a tag has been cached, the thread should periodically (1 sec intervals?)
# check if a different tag is on the reader (->instantly invalidate cache and
# cache new tag) or no tag is available anymore (keep cache for a short while,
# to allow users to scan tag and then click buttons on the user interface,
# instead of doing both actions in parallel)
# CALLBACK_READER_STATE_CHANGED may conflict with the periodical polling, so
# reliabilty testing should be performed for the callback.
# if the callback is reliable in all cases, then polling may not be needed in
# the first place
