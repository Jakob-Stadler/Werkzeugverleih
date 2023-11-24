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
import werkzeugverleih.database as db
import werkzeugverleih.camera as cam
import werkzeugverleih.webserver as webserver
import werkzeugverleih.routine as routine
import werkzeugverleih.main as main
import pytest
from os import remove
from os.path import exists


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

  cfg.FLASK_CONFIG_LOCATION = 'tests/scratch/flask.cfg'

  log.initialize_logger()

  cfg.DATABASE_FILE_LOCATION = ':memory:'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_default_flask_config_if_missing():
  cfg.FLASK_CONFIG_LOCATION = 'tests/scratch/flask.cfg'
  try:
    remove(cfg.FLASK_CONFIG_LOCATION)
  except FileNotFoundError:
    pass

  main.default_flask_config_if_missing()
  assert exists(cfg.FLASK_CONFIG_LOCATION)
  main.default_flask_config_if_missing()
  assert exists(cfg.FLASK_CONFIG_LOCATION)

  cfg.FLASK_CONFIG_LOCATION = 'tests/scratch/nonexistant_folder/flask.cfg'

  with pytest.raises(SystemExit):
    main.default_flask_config_if_missing()

  assert not exists(cfg.FLASK_CONFIG_LOCATION)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def main_mocks():
  # nop function, all subroutines are tested individually
  def mock_pass(*args, **kwargs):
    pass

  original_initialize_logger = log.initialize_logger
  original_default_flask_config = main.default_flask_config_if_missing
  original_initialize_connection = db.initialize_connection
  original_create_tables = db.create_tables
  original_initialize_camera = cam.initialize_camera
  original_start_routine = routine.start_routine
  original_start_webserver = webserver.start_webserver
  original_stop_routine = routine.stop_routine
  original_close_connection = db.close_connection

  log.initialize_logger = mock_pass
  main.default_flask_config_if_missing = mock_pass
  db.initialize_connection = mock_pass
  db.create_tables = mock_pass
  cam.initialize_camera = mock_pass
  routine.start_routine = mock_pass
  webserver.start_webserver = mock_pass
  routine.stop_routine = mock_pass
  db.close_connection = mock_pass

  yield

  log.initialize_logger = original_initialize_logger
  main.default_flask_config_if_missing = original_default_flask_config
  db.initialize_connection = original_initialize_connection
  db.create_tables = original_create_tables
  cam.initialize_camera = original_initialize_camera
  routine.start_routine = original_start_routine
  webserver.start_webserver = original_start_webserver
  routine.stop_routine = original_stop_routine
  db.close_connection = original_close_connection
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_main(main_mocks):
  cfg.config_file = 'tests/scratch/test.json'

  try:
    remove(cfg.config_file)
  except FileNotFoundError:
    pass

  with pytest.raises(SystemExit):
    main.main()

  open(cfg.config_file, 'w').close()

  with pytest.raises(SystemExit):
    main.main()
# ------------------------------------------------------------------------------
