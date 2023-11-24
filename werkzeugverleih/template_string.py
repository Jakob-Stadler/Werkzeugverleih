"""
name:
  Werkzeugverleih Template String Builders
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Collection of template string builders for other modules
dependencies:
  -
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
# ------------------------------------------------------------------------------


# shared imports ---------------------------------------------------------------
from string import Template
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def log_filename(formatted_date: str) -> str:
  '''Template string builder for the filename of log files.

  Based on the value of cfg.LOG_FILENAME_TEMPLATE
  '''
  return Template(cfg.LOG_FILENAME_TEMPLATE).substitute(date=formatted_date)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def log_filepath(filename: str) -> str:
  '''Template string builder for the location of the log files.

  Based on the value of cfg.LOG_FILEPATH_TEMPLATE
  '''
  return Template(cfg.LOG_FILEPATH_TEMPLATE).substitute(filename=filename)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def backup_filename(date: str) -> str:
  '''Template string builder for the filename of the database backup.

  Based on the value of cfg.BACKUP_FILENAME_TEMPLATE
  '''
  return Template(cfg.BACKUP_FILENAME_TEMPLATE).substitute(date=date)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def backup_filepath(filename: str) -> str:
  '''Template string builder for the location of the database backup.

  Based on the value of cfg.BACKUP_FILEPATH_TEMPLATE
  '''
  return Template(cfg.BACKUP_FILEPATH_TEMPLATE).substitute(filename=filename)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def current_user(user: dict) -> str:
  '''Template string builder for the user info to display in the header section.

  Based on the value of cfg.CURRENT_USER_TEMPLATE
  '''
  if user is None:
    return ''
  else:
    try:
      given_name = user.get('given_name', '')
      surname = user.get('surname', '')
      room = user.get('room', '')
    except AttributeError:
      return ''

    return Template(cfg.CURRENT_USER_TEMPLATE).substitute(
                                                given_name=given_name,
                                                surname=surname,
                                                room=room
                                              )
# ------------------------------------------------------------------------------
# ==============================================================================
