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
  Collection of tests for werkzeugverleih.database
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import werkzeugverleih.database as database
import pytest


# ------------------------------------------------------------------------------
@pytest.fixture(scope='module', autouse=True)
def default_statements():
  cfg.LOG_LEVEL = 'debug'
  cfg.LOG_FILENAME_TEMPLATE = 'log_${date}.log'
  cfg.LOG_FILEPATH_TEMPLATE = 'tests/scratch/${filename}'
  cfg.DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  cfg.LOGGING_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
  cfg.INACTIVITY_LIMIT_DAYS = 1

  cfg.DATABASE_FILE_LOCATION = ':memory:'

  log.initialize_logger()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_unix_timestamp():
  from time import time
  count = 0
  for i in range(10):
    t_0 = int(time())
    t_1 = database.unix_timestamp()
    print('Timestamps:', t_0, t_1)
    count += 1 if t_0 == t_1 else 0

  assert count >= 8  # correct timestamp at least 80% of the time
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_000_database_basics():
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.create_tables()
  assert database.db_connection is not None
  database.close_connection()
  assert database.db_connection is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_double_initialize_connection():
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  with pytest.raises(ValueError):
    database.initialize_connection()
  # don't forget to close connection again!
  database.close_connection()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_double_close_connection():
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.close_connection()
  # fail silently when already closed
  database.close_connection()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def db_fixture():
  cfg.DATABASE_FILE_LOCATION = ':memory:'
  database.initialize_connection()
  database.create_tables()
  yield
  database.close_connection()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_backup_database(db_fixture):
  database.backup_database('tests/scratch/backup.db')
  from os.path import exists
  assert exists('tests/scratch/backup.db')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_user(db_fixture):
  b = database.add_user('a', 'b', 'c', 'd')
  assert b
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_user_duplicate(db_fixture):
  b = database.add_user('a', 'b', 'c', 'd')
  c = database.add_user('a', 'b', 'c', 'd')
  assert b and not c
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_user_None(db_fixture):
  b = database.add_user(None, None, None, None)
  assert not b
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fill_users(db_fixture):
  database.add_user('a', 'b', 'c', 'd')
  database.add_user('e', 'f', 'g', 'h')
  database.add_user('i', 'j', 'k', 'l')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_user(fill_users):
  u = database.get_user('e')
  e = { 'nfc_id': 'e',
        'given_name': 'f',
        'surname': 'g',
        'room': 'h'}

  assert all(u[k] == e[k] for k in e)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_user_None(fill_users):
  u = database.get_user('z')
  assert u is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_users(fill_users):
  ul = database.get_users()
  el = [{ 'nfc_id': 'a',
          'given_name': 'b',
          'surname': 'c',
          'room': 'd'},
        { 'nfc_id': 'e',
          'given_name': 'f',
          'surname': 'g',
          'room': 'h'},
        { 'nfc_id': 'i',
          'given_name': 'j',
          'surname': 'k',
          'room': 'l'}]

  assert all(
              (
                all(u[k] == e[k] for k in e)
                for u in ul if u['nfc_id'] == e['nfc_id'])
              for e in el)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_update_user(fill_users):
  database.update_user('e', 'x', 'y', 'z', admin=True)

  u = database.get_user('e')
  e = { 'nfc_id': 'e',
        'given_name': 'x',
        'surname': 'y',
        'room': 'z',
        'admin': 1}

  assert all(u[k] == e[k] for k in e)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_user(fill_users):
  d = database.delete_user('e')
  u = database.get_user('e')
  assert d == 1 and u is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_user_nonexistant(fill_users):
  d = database.delete_user('z')
  assert d == 0
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_inactive_users(db_fixture):
  # fake timestamp to 1970
  def fixed_time():
    return 0

  database.unix_timestamp = fixed_time

  database.add_user('a', 'b', 'c', 'd')  # first entry admin will not be deleted
  database.add_user('e', 'f', 'g', 'h')
  database.add_user('i', 'j', 'k', 'l')

  from time import time

  def real_time():
    return int(time())

  database.unix_timestamp = real_time

  database.add_user('m', 'n', 'o', 'p')

  d = database.delete_inactive_users(real_time() - 3600)
  ul = database.get_users()

  assert d == 2 and all((u['nfc_id'] in ['a', 'm']) for u in ul)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_transaction(db_fixture):
  t = database.add_transaction('a', b'DATA')
  assert t is not None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_transaction_nfc_None(db_fixture):
  t = database.add_transaction(None, b'DATA')
  assert t is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_transaction_image_None(db_fixture):
  t = database.add_transaction('a', None)
  assert t is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_transaction_nfc_malformed(db_fixture):
  t = database.add_transaction([], b'DATA')
  assert t is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_add_transaction_image_malformed(db_fixture):
  t = database.add_transaction('a', [])
  assert t is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fill_transactions(db_fixture):
  database.add_transaction('a', b'DATA')
  t_id = database.add_transaction('b', b'BASE')
  database.add_transaction('b', b'DROP')
  database.add_transaction('a', b'TABLE')

  yield t_id
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_transactions(fill_transactions):
  tl = database.get_transactions()
  el = [{ 'transaction_id': 0,
          'nfc_id': 'a',
          'image': b'DATA'},
        { 'transaction_id': 1,
          'nfc_id': 'b',
          'image': b'BASE'} ]

  assert all(
              (
                all(t[k] == e[k] for k in e)
                for t in tl if t['transaction_id'] == e['transaction_id'])
              for e in el)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_transaction(fill_transactions):
  t_id = fill_transactions

  t = database.get_transaction(t_id)
  e = { 'nfc_id': 'b',
        'image': b'BASE'}

  assert all(t[k] == e[k] for k in e)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_transaction_nonexistant(fill_transactions):
  t = database.get_transaction(999999)
  assert t is None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_transactions_from_nfc_id(fill_transactions):
  tl = database.get_transactions_from_nfc_id('b')
  el = [{ 'transaction_id': 1,
          'nfc_id': 'b',
          'image': b'BASE'},
        { 'transaction_id': 2,
          'nfc_id': 'b',
          'image': b'DROP'} ]

  assert all(
              (
                all(t[k] == e[k] for k in e)
                for t in tl if t['transaction_id'] == e['transaction_id'])
              for e in el)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_transactions_from_nfc_id_nonexitant(fill_transactions):
  tl = database.get_transactions_from_nfc_id('c')
  assert tl == []
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_transaction(fill_transactions):
  t_id = fill_transactions
  t = database.get_transaction(t_id)
  rk = t['removal_key']

  r = database.delete_transaction(t_id, rk)
  assert r == 1
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_transaction_nonexistant(fill_transactions):
  t_id = fill_transactions
  r = database.delete_transaction(t_id, None)
  assert r == 0
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_safe_delete_transaction(fill_transactions):
  t_id = fill_transactions

  t = database.get_transaction(t_id)
  rk = t['removal_key']

  r = database.safe_delete_transaction(t_id, rk, 'b')
  assert r == 1
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_safe_delete_transaction_nonexistant(fill_transactions):
  t_id = fill_transactions

  t = database.get_transaction(t_id)
  rk = t['removal_key']

  r = database.safe_delete_transaction(t_id, rk, None)
  assert r == 0
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_unsafe_delete_transaction(fill_transactions):
  t_id = fill_transactions

  r = database.unsafe_delete_transaction(t_id)
  assert r == 1
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_unsafe_delete_transaction_nonexistant(fill_transactions):
  r = database.unsafe_delete_transaction(None)
  assert r == 0
# ------------------------------------------------------------------------------
