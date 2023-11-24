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
  Collection of tests for werkzeugverleih.routine
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import werkzeugverleih.routine as routine
import werkzeugverleih.database as database
import pytest


# ------------------------------------------------------------------------------
@pytest.fixture(scope='module', autouse=True)
def default_statements():
  cfg.LOG_LEVEL = 'debug'
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  cfg.LOG_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.BACKUP_FILENAME_TEMPLATE = 'backup_${date}.db'
  cfg.BACKUP_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'

  cfg.DATE_FORMAT = "%Y-%m-%d"
  cfg.DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'

  cfg.KEEP_BACKUPS_FOR_X_DAYS = 1
  cfg.KEEP_LOGS_FOR_X_DAYS = 1
  cfg.INACTIVITY_LIMIT_DAYS = 1

  log.initialize_logger()

  cfg.DATABASE_FILE_LOCATION = ':memory:'
# ------------------------------------------------------------------------------


def test_tomorrow_debug():
  cfg.DEBUG = True
  import datetime as dt
  from datetime import timedelta

  count = 0
  for i in range(10):
    t_0 = (dt.datetime.now() + timedelta(minutes=1)).timestamp()
    t_1 = routine.tomorrow()
    print('Timestamps:', t_0, t_1)
    count += 1 if round(t_0) == round(t_1) else 0

  assert count >= 8  # correct timestamp at least 80% of the time


def test_tomorrow_prod():
  cfg.DEBUG = False
  import datetime as dt
  from datetime import timedelta

  count = 0
  for i in range(10):
    t_0 = dt.datetime.combine(
            dt.date.today() + timedelta(days=1),
            dt.time(0, 1, 0)
          ).timestamp()
    t_1 = routine.tomorrow()
    print('Timestamps:', t_0, t_1)
    count += 1 if round(t_0) == round(t_1) else 0

  assert count >= 8  # correct timestamp at least 80% of the time


def test_get_formatted_days_elapsed_0():
  from datetime import date
  cfg.DATE_FORMAT = "%Y-%m-%d"

  d_0 = [date.today().strftime("%Y-%m-%d")]
  d_1 = routine.get_formatted_days_elapsed(0)

  assert d_0 == d_1


def test_get_formatted_days_elapsed_1():
  from datetime import date, timedelta
  cfg.DATE_FORMAT = "%Y-%m-%d"

  d_0 = [
    date.today().strftime("%Y-%m-%d"),
    (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")]
  d_1 = routine.get_formatted_days_elapsed(1)

  assert d_0 == d_1


def test_get_formatted_days_elapsed_None():
  from datetime import date
  cfg.DATE_FORMAT = "%Y-%m-%d"

  d_0 = [date.today().strftime("%Y-%m-%d")]
  d_1 = routine.get_formatted_days_elapsed(None)

  assert d_0 == d_1


def test_backup_db():
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.create_tables()

  routine.backup_db()

  database.close_connection()


def test_remove_backups():
  cfg.BACKUP_FILENAME_TEMPLATE = 'backup_${date}.db'
  cfg.BACKUP_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.KEEP_BACKUPS_FOR_X_DAYS = 1

  cfg.DATE_FORMAT = "%Y-%m-%d"

  date_list = routine.get_formatted_days_elapsed(3)

  from werkzeugverleih.template_string import backup_filename, backup_filepath
  path_list = [backup_filepath(backup_filename(d)) for d in date_list]

  for path in path_list:
    open(path, 'a').close()

  routine.remove_backups()

  from os.path import exists

  assert exists(path_list[0])
  assert exists(path_list[1])
  assert not exists(path_list[2])
  assert not exists(path_list[3])


def test_remove_inactive_users():
  cfg.INACTIVITY_LIMIT_DAYS = 1
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.create_tables()

  from time import time
  database.db_connection.executemany(
    'INSERT INTO users(nfc_id, admin, last_access)'
    'VALUES (?, 0, ?)', [
      ('A', 0),  # <- will be deleted
      ('B', time() - 48 * 60 * 60),  # <- will be deleted
      ('C', time() - 12 * 60 * 60),  # <- will remain
      ('D', time())  # <- will remain
    ]
  )

  routine.remove_inactive_users()

  ul = database.get_users()

  database.close_connection()

  print(ul)

  assert all(
    (u['nfc_id'] in ['C', 'D'] and u['nfc_id'] not in ['A', 'B'])
    for u in ul)


def test_remove_old_logs():
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  cfg.LOG_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.KEEP_LOGS_FOR_X_DAYS = 1

  cfg.DATE_FORMAT = "%Y-%m-%d"

  date_list = routine.get_formatted_days_elapsed(3)

  from werkzeugverleih.template_string import log_filepath, log_filename
  path_list = [log_filepath(log_filename(d)) for d in date_list]

  for path in path_list:
    open(path, 'a').close()

  routine.remove_old_logs()

  from os.path import exists

  assert exists(path_list[0])
  assert exists(path_list[1])
  assert not exists(path_list[2])
  assert not exists(path_list[3])


def test_daily_job():
  assert routine.daily_event is None

  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.create_tables()

  routine.daily_job()

  database.close_connection()

  assert routine.daily_event is not None
  # cleanup
  routine.scheduler.cancel(routine.daily_event)
  routine.daily_event = None


def test_daily_schedule():
  original_daily_job = routine.daily_job
  original_tomorrow = routine.tomorrow

  def mock_daily_job():
    routine.keep_running = False

  def mock_tomorrow():
    from datetime import datetime, timedelta
    return (datetime.now() + timedelta(seconds=1)).timestamp()

  routine.daily_job = mock_daily_job
  routine.tomorrow = mock_tomorrow

  routine.daily_schedule()

  routine.daily_job = original_daily_job
  routine.tomorrow = original_tomorrow


def test_start_stop_routine():
  original_daily_job = routine.daily_job

  def mock_daily_job():
    routine.keep_running = False

  routine.daily_job = mock_daily_job

  # Start
  routine.start_routine()
  # Restart
  routine.start_routine()
  # Stop
  routine.stop_routine()

  routine.daily_job = original_daily_job


def test_start_stop_routine_no_event():
  original_daily_schedule = routine.daily_schedule

  def mock_daily_schedule():
    print('in mock_daily_schedule')
    pass

  routine.daily_schedule = mock_daily_schedule
  routine.daily_event = None

  # Start
  routine.start_routine()
  # Restart
  routine.start_routine()
  # Stop
  routine.stop_routine()

  routine.daily_schedule = original_daily_schedule
