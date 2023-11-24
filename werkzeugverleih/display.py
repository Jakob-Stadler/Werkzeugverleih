"""
name:
  Werkzeugverleih Display Management
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Save energy by turning off the screen when not in use!
dependencies:
  -
"""
from pynput.mouse import Controller

def wake_up_screen_via_NFC():
    mouse = Controller()
    mouse.move(1,1)

# ------------------------------------------------------------------------------

# This module should handle:
# 1. turn off screen after period of inactivity
# 2. turn screen back on via touch event
# 3. turn screen back on via nfc event

# an alternative for 1. and 2. may be to use xscreensaver instead
# and only handle case 3. in python with `xset s` / `xset dpms`
