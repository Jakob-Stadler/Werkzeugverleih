"""
name:
  Werkzeugverleih Routine Maintenance
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Executes housekeeping tasks on a (daily) schedule.
dependencies:
  -
"""

# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
from werkzeugverleih.log import log
import werkzeugverleih.database as db
from werkzeugverleih.template_string import ( log_filename,
                                              log_filepath,
                                              backup_filename,
                                              backup_filepath )
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from typing import List
# ------------------------------------------------------------------------------


# HELPER FUNCTIONS =============================================================
import datetime as dt
from datetime import timedelta
# ------------------------------------------------------------------------------
def tomorrow() -> float:
  '''return the timestamp of tomorrow 00:01:00'''

  if cfg.DEBUG:
    # quickly test the routine thread functionality by executing the job once
    # a minute instead of once a day
    return (dt.datetime.now() + timedelta(minutes=1)).timestamp()

  return dt.datetime.combine(
            dt.date.today() + timedelta(days=1),
            dt.time(0, 1, 0)
          ).timestamp()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_formatted_days_elapsed(days: int = 0) -> List[str]:
  '''return list of formatted strings with dates,
  starting from today and going back to `days` days in the past.
  Format is determind by `cfg.DATE_FORMAT`.

  arguments:
  + `days` -- integer, number of days in the past

  If you only need a formatted representation of today's date, use
  `get_formatted_days_elapsed(0)[0]`
  If today's date is not welcome in the output, use
  `get_formatted_days_elapsed(days)[1:]`
  '''
  try:
    date_generator = (dt.date.today() - timedelta(days=i)
                      for i in range(days + 1))
  except TypeError:  # Fallback to single day (incorrect parameter type)
    date_generator = [dt.date.today()]
    log('routine.get_formatted_days_elapsed(): incorrect type detected for '
        f'argument days= {days}', level='warning')
  return [d.strftime(cfg.DATE_FORMAT) for d in date_generator]
# ------------------------------------------------------------------------------
# ==============================================================================


# SCHEDULE FUNCTIONS ===========================================================
from sched import scheduler as sched_scheduler
from time import time, sleep
# declared globally in order to make them externally modifiable
scheduler = sched_scheduler(time, sleep)
daily_event = None
keep_running = True
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def cancel_daily_event() -> None:
  global daily_event
  try:
    scheduler.cancel(daily_event)
    daily_event = None
  except (ValueError, AttributeError):
    # No event scheduled, just reset the variable and move on
    daily_event = None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def daily_schedule() -> None:
  '''worker function for the daily routine schedule'''
  global daily_event, keep_running

  time_formatted = (dt.datetime.utcfromtimestamp(
                      tomorrow()
                    ).strftime(cfg.DATETIME_FORMAT))
  log('routine.daily_schedule(): scheduling next daily_job for '
      f'{time_formatted}', level='info')

  daily_event = scheduler.enterabs(time=tomorrow(), priority=1,
                                    action=daily_job)
  while keep_running:
    next_deadline = scheduler.run(blocking=False)
    if next_deadline is not None:
      sleep(min(1, next_deadline))
    else:
      sleep(1)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def daily_job() -> None:
  '''maintenance function that gets called once a day

  Tasks to do:
  + backup database
  + delete old database backups
  + remove inactive users from database
  + delete old logs
  '''
  global daily_event

  log('routine.daily_job(): starting daily job', level='info')

  # backup database
  backup_db()

  # delete old backups older than KEEP_BACKUPS_FOR_X_DAYS
  remove_backups()

  # remove inactive users longer than INACTIVITY_LIMIT_DAYS
  remove_inactive_users()

  # delete old logs older than KEEP_LOGS_FOR_X_DAYS
  remove_old_logs()

  time_formatted = (dt.datetime.utcfromtimestamp(
                      tomorrow()
                    ).strftime(cfg.DATETIME_FORMAT))
  log('routine.daily_job(): scheduling next daily_job for '
      f'{time_formatted}', level='info')

  daily_event = scheduler.enterabs(time=tomorrow(), priority=1,
                                      action=daily_job)
# ------------------------------------------------------------------------------


# helper functions for daily_job()
# ------------------------------------------------------------------------------
def backup_db() -> None:
  '''backup database

  helper function for daily_job()
  '''
  log('routine.backup_db(): backup database', level='debug')

  formatted_date = get_formatted_days_elapsed(0)[0]

  backup_location = backup_filepath(backup_filename(formatted_date))

  db.backup_database(backup_location)

  log(f'routine.backup_db(): saved db backup to {backup_location}',
      level='info')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from os import scandir, remove
import fnmatch
def remove_backups() -> None:
  '''delete old backups older than `KEEP_BACKUPS_FOR_X_DAYS`

  helper function for daily_job()
  '''
  log('routine.remove_backups(): remove old backups', level='debug')

  # get list of filenames to keep
  valid_dates = get_formatted_days_elapsed(cfg.KEEP_BACKUPS_FOR_X_DAYS)
  valid_filenames = [backup_filename(date) for date in valid_dates]

  with scandir(backup_filepath('')) as scan:

    # build list of names for all elements in scan directory that are files
    # inner list could be replaced with `filter(lambda e: e.is_file(), scan)`
    file_list = [file.name for file in [e for e in scan if e.is_file()]]

    pattern = backup_filename('*')
    for filename in fnmatch.filter(file_list, pattern):

      if filename not in valid_filenames:
        remove(backup_filepath(filename))
        log('routine.remove_backups(): removed db backup '
            f'{backup_filepath(filename)}', level='info')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def remove_inactive_users() -> None:
  '''remove users that are inactive for longer than `INACTIVITY_LIMIT_DAYS`

  helper function for daily_job()
  '''
  log('routine.remove_inactive_users(): remove inactive users', level='debug')

  cutoff_time = int(time() - (cfg.INACTIVITY_LIMIT_DAYS * 24 * 60 * 60))

  db.delete_inactive_users(cutoff_time)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def remove_old_logs() -> None:
  '''delete old logs older than `KEEP_LOGS_FOR_X_DAYS`

  helper function for daily_job()
  '''
  log('routine.remove_old_logs(): remove old logs', level='debug')

  # get list of filenames to keep
  valid_dates = get_formatted_days_elapsed(cfg.KEEP_LOGS_FOR_X_DAYS)
  valid_filenames = [log_filename(date) for date in valid_dates]

  with scandir(log_filepath('')) as scan:

    # build list of names for all elements in scan directory that are files
    # inner list could be replaced with `filter(lambda e: e.is_file(), scan)`
    file_list = [file.name for file in [e for e in scan if e.is_file()]]

    pattern = log_filename('*')
    for filename in fnmatch.filter(file_list, pattern):

      if filename not in valid_filenames:
        remove(log_filepath(filename))
        log('routine.remove_old_logs(): removed log file '
            f'{log_filepath(filename)}', level='info')
# ------------------------------------------------------------------------------
# ==============================================================================


# THREAD FUNCTIONS =============================================================
from threading import Thread
routine_thread = None
# ------------------------------------------------------------------------------
def start_routine() -> None:
  '''start the routine thread'''
  global routine_thread, keep_running, daily_event

  if routine_thread:
    log('routine.start_routine(): restarting thread: '
        'stopping old thread beforehand', level='debug')

    keep_running = False
    cancel_daily_event()

    routine_thread.join(timeout=3)
    routine_thread = None

  log('routine.start_routine(): start thread', level='debug')

  keep_running = True
  routine_thread = Thread(target=daily_schedule)
  routine_thread.start()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def stop_routine() -> None:
  '''start the routine thread'''
  global routine_thread, keep_running, daily_event

  log('routine.stop_routine(): stop thread', level='debug')

  keep_running = False
  cancel_daily_event()

  routine_thread.join(timeout=3)
# ------------------------------------------------------------------------------
# ==============================================================================
