"""
name:
  Werkzeugverleih Database Management
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Interface between other modules and database to make the rest of the
  package independent of database implementation.
dependencies:
  -
"""


# intra-package imports --------------------------------------------------------
import werkzeugverleih.config as cfg
from werkzeugverleih.log import log
# ------------------------------------------------------------------------------


from typing import Callable, Any, List


# HELPER FUNCTIONS =============================================================
# ------------------------------------------------------------------------------
from time import time
def unix_timestamp() -> int:
  '''integer, return seconds since Unix epoch (1970-01-01 00:00:00 UTC)'''
  return int(time())
# ------------------------------------------------------------------------------
# ==============================================================================


# THREAD SAFETY DECORATOR ======================================================
from threading import Lock
db_lock = Lock()
# ------------------------------------------------------------------------------
from functools import wraps
def lock_and_release(func: Callable[..., Any]) -> Callable[..., Any]:
  '''wrapper for thread-safe database access,
  use as @decorator

  arguments:
  + `func` -- the function to be wrapped
  '''
  @wraps(func)
  def wrapper(*args, **kwargs):
    # log('database.lock_and_release(): acquiring lock on database',
    #      level='debug')
    db_lock.acquire()
    try:
      r = func(*args, **kwargs)
    finally:
      # log('database.lock_and_release(): releasing lock on database',
      #      level='debug')
      db_lock.release()
    return r
  return wrapper
# ------------------------------------------------------------------------------
# ==============================================================================


# DATABASE FUNCTIONS ===========================================================
import sqlite3
db_connection = None
# ------------------------------------------------------------------------------
@lock_and_release
def initialize_connection() -> None:
  '''connect to sqlite3 database located in cfg.DATABASE_FILE_LOCATION'''

  log('database.initialize_connection(): to file '
      f'{cfg.DATABASE_FILE_LOCATION}', level='debug')

  global db_connection
  if db_connection is None:
    db_connection = sqlite3.connect(cfg.DATABASE_FILE_LOCATION,
                                    check_same_thread=False)
    db_connection.row_factory = sqlite3.Row
  else:
    raise ValueError
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def close_connection() -> None:
  '''disconnect from database and close connection, fail silently'''

  log('database.close_connection()', level='debug')

  global db_connection
  try:
    db_connection.close()
  except AttributeError:
    pass
  finally:
    db_connection = None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def backup_database(backup_location: str) -> None:
  '''creates a backup of the active database in `backup_location`'''

  log(f'database.backup_database(): to file "{backup_location}"',
      level='debug')

  global db_connection
  with sqlite3.connect(backup_location) as backup_connection:
    db_connection.backup(backup_connection)

  log('database.backup_database(): finished database backup to '
      f'"{backup_location}"', level='info')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def create_tables() -> None:
  '''ensure existance of necessary tables'''

  log("database.create_tables(): 'users' and 'transactions' if missing",
      level='debug')

  global db_connection
  c = db_connection.cursor()

  c.execute( '''CREATE TABLE IF NOT EXISTS users(
                  nfc_id TEXT PRIMARY KEY NOT NULL,
                  given_name TEXT,
                  surname TEXT,
                  room TEXT,
                  admin INTEGER,
                  date_registered INTEGER,
                  last_access INTEGER)''')

  c.execute( '''CREATE TABLE IF NOT EXISTS transactions(
                  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                  nfc_id TEXT,
                  transaction_time INTEGER,
                  removal_key TEXT,
                  image BLOB)''')

  db_connection.commit()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def add_user(
    nfc_id: str,
    given_name: str,
    surname: str,
    room: str
  ) -> bool:
  '''add row to 'users' table

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  + `given_name` -- string
  + `surname` -- string
  + `room` -- string

  additional non user-defined values for database:
  + `admin` -- integer 0 (except for first user in database)
  + `date_registered` -- integer, current timestamp
  + `last_access` -- integer, current timestamp
  '''

  log(f'database.add_user(): with data for nfc_id {nfc_id}',
      level='debug')

  global db_connection
  c = db_connection.cursor()

  # first user in database gets admin privileges by default
  c.execute('SELECT COUNT(*) FROM users')
  admin = 1 if (c.fetchone()[0] == 0) else 0

  params = (nfc_id,
                given_name,
                surname,
                room,
                admin,
                unix_timestamp(),
                unix_timestamp())

  try:
    c.execute( '''INSERT INTO users
                  (nfc_id, given_name, surname, room, admin,
                  date_registered, last_access)
                  VALUES (?, ?, ?, ?, ?, ?, ?)''', params)

    db_connection.commit()

    log('database.add_user(): successfully added user data for nfc_id '
        f'{nfc_id}', level='info')

    return True

  except sqlite3.IntegrityError:

    log('database.add_user(): failed to add user data for nfc_id '
        f'{nfc_id} (IntegrityError)', level='warning')

    return False
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def get_user(nfc_id: str) -> dict:
  '''search the 'users' table for row with 'nfc_id'=`nfc_id`,
  update 'last_access' of found row with current timestamp

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  '''

  log(f'database.get_user(): data for nfc_id {nfc_id}', level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (nfc_id,)

  for row in c.execute('SELECT * FROM users WHERE nfc_id=?', params):

    update_parameters = (unix_timestamp(), nfc_id)
    c.execute( '''UPDATE users
                  SET last_access=?
                  WHERE nfc_id=?''', update_parameters)

    db_connection.commit()

    return dict(zip(row.keys(), row))

  # no rows -> None
  return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def get_users() -> List[dict]:
  '''return a list of all users currently in database

  data from a single user is stored as dict, accessible via keys:
  `nfc_id`, `given_name`, `surname`, `room`, `admin`, `date_registered`,
  `last_access`
  '''

  log("database.get_users(): list of all users' data", level='debug')

  global db_connection
  c = db_connection.cursor()

  rowlist = []
  for row in c.execute('SELECT * FROM users'):
    rowlist.append(dict(zip(row.keys(), row)))

  return rowlist
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def update_user(
    nfc_id: str,
    given_name: str,
    surname: str,
    room: str,
    admin: bool = False
  ) -> None:
  '''change the registration data of an existing row in table 'users'

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  + `given_name` -- string
  + `surname` -- string
  + `room` -- string
  + `admin` -- bool
  '''

  log(f'database.update_user(): change data for nfc_id {nfc_id}',
      level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (given_name,
                surname,
                room,
                1 if admin else 0,
                nfc_id)

  c.execute('''UPDATE users
                SET given_name=?, surname=?, room=?, admin=?
                WHERE nfc_id=?''', params)

  db_connection.commit()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def delete_user(nfc_id: str) -> int:
  '''remove a row from table 'users' where 'nfc_id'=`nfc_id`,
  returns the number of deleted rows (0 or 1)

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  '''

  log(f'database.delete_user(): with nfc_id {nfc_id}', level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (nfc_id,)

  result = c.execute('DELETE FROM users WHERE nfc_id=?', params)

  db_connection.commit()

  if result.rowcount:
    log(f'database.delete_user(): removed nfc_id {nfc_id}', level='info')
  else:
    log(f'database.delete_user(): failed to remove nfc_id {nfc_id}',
        level='warning')

  return result.rowcount
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def delete_inactive_users(inactivity_timestamp: int) -> int:
  '''remove rows from table 'users' where 'last_access'<=`inactivity_timestamp`,
  with the exception of admins

  returns the number of deleted rows

  arguments:
  + `inactivity_timestamp` -- integer,
  timestamp of when a user counts as inactive
  '''

  log(f'database.delete_inactive_users(): timestamps<={inactivity_timestamp}',
      level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (inactivity_timestamp,)

  rowlist = []
  rowlist = c.execute('''SELECT users.nfc_id FROM users
                        LEFT JOIN transactions
                        ON users.nfc_id = transactions.nfc_id
                        WHERE transactions.nfc_id IS NULL
                          AND users.last_access<=?
                          AND users.admin=0''', params)

  nfc_list = [dict(zip(row.keys(), row)).get('nfc_id') for row in rowlist]

  # nfc_list needs to be repacked into a list of tuples (nfc_id, ), since
  # executemany will interpret a string as char-iterable if it is not supplied
  # with an iterable of an iterable of a string (here: list of tuple of string)
  result = c.executemany('DELETE FROM users WHERE nfc_id=?',
                          [(nfc_id, ) for nfc_id in nfc_list])

  db_connection.commit()

  log("database.delete_inactive_users(): removed from table 'users': "
      f"{result.rowcount} row(s): {nfc_list}", level='info')

  return result.rowcount
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from os import urandom
from hashlib import sha256
@lock_and_release
def add_transaction(nfc_id: str, image: bytes) -> dict:
  '''add row to 'transactions' table,
  return transaction_id of newly created row

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  + `image` -- binary string, e.g. b'DATA'

  additional non user-defined values for database:
  + `transaction_id` -- unique auto generated integer
  + `transaction_time` -- integer, current timestamp
  + `removal_key` -- string, random SHA256 Hash hexdigest associated with
  transaction
  '''

  log(f'database.add_transaction(): data for nfc_id {nfc_id}', level='debug')

  if nfc_id is None:
    log("database.add_transaction(): can't add transaction without "
        "valid nfc_id", level='warning')
    return None

  if image is None:
    log(f"database.add_transaction(): can't add empty image (None) for "
        f"nfc_id {nfc_id}", level='warning')
    return None

  global db_connection
  c = db_connection.cursor()

  removal_key = sha256(urandom(32)).hexdigest()

  try:
    params = (nfc_id,
                  unix_timestamp(),
                  removal_key,
                  sqlite3.Binary(image))
  except TypeError:
    log(f"database.add_transaction(): invalid image data format for "
        f"nfc_id {nfc_id}", level='warning')
    return None

  try:
    c.execute( '''INSERT INTO transactions
                  (transaction_id, nfc_id, transaction_time, removal_key, image)
                  VALUES (NULL, ?, ?, ?, ?)''', params)

    params = (c.lastrowid,)

    db_connection.commit()

    row = c.execute('SELECT * FROM transactions WHERE ROWID=?',
                    params).fetchone()
    ''' # uncommented until a way is found to trigger this for code coverage
    if row is None:
      log('database.add_transaction(): failed to add transaction for nfc_id '
          f'{nfc_id}', level='warning')
      return None
    '''
    row_dict = dict(zip(row.keys(), row))
    log('database.add_transaction(): added transaction with id '
        f'{row_dict.get("transaction_id")} for '
        f'nfc_id {row_dict.get("nfc_id")}', level='debug')
    return row_dict.get('transaction_id')

  except sqlite3.InterfaceError:

    log('database.add_transaction(): failed to add transaction for nfc_id '
        f'{nfc_id} (InterfaceError)', level='warning')

    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def get_transactions() -> List[dict]:
  '''return a list of all transactions currently in database

  data from a single transaction is stored as dict, accessible via keys:
  `transaction_id`, `image`, `nfc_id`, `transaction_time`, `removal_key`
  '''

  log('database.get_transactions(): list of all transactions', level='debug')

  global db_connection
  c = db_connection.cursor()

  rowlist = []
  for row in c.execute('SELECT * FROM transactions'):
    rowlist.append(dict(zip(row.keys(), row)))

  return rowlist
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def get_transaction(transaction_id: int) -> dict:
  '''returns a single transaction from database identified by 'transaction_id'

  data is stored as dict, accessible via keys:
  `transaction_id`, `image`, `nfc_id`, `transaction_time`, `removal_key`

  arguments:
  + `transaction_id` -- integer, unique auto generated primary key
  '''

  log(f'database.get_transaction(): data for transaction_id {transaction_id}',
      level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (transaction_id,)

  for row in c.execute('''SELECT * FROM transactions
                          WHERE transaction_id=?''', params):
    return dict(zip(row.keys(), row))

  # no rows -> None
  return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def get_transactions_from_nfc_id(nfc_id: str) -> List[dict]:
  '''return a list of transactions currently in database,
  filtered by 'nfc_id'=`nfc_id`

  data from a single transaction is stored as dict, accessible via keys:
  `transaction_id`, `image`, `nfc_id`, `transaction_time`, `removal_key`

  arguments:
  + `nfc_id` -- string, NFC ID formatted as hex string
  '''

  log('database.get_transactions_from_nfc_id(): list of transactions from '
      f'nfc_id {nfc_id}', level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (nfc_id,)

  rowlist = []
  for row in c.execute('''SELECT * FROM transactions
                          WHERE nfc_id=?''', params):

    rowlist.append(dict(zip(row.keys(), row)))

  return rowlist
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def delete_transaction(
    transaction_id: int,
    removal_key: str
  ) -> int:
  '''default variant of delete_transaction(), removal_key required

  remove a row from table 'transactions' where both
  'transaction_id'=`transaction_id` AND 'removal_key'=`removal_key`

  returns the number of deleted rows (0 or 1)

  arguments:
  + `transaction_id` -- integer, unique auto generated primary key
  + `removal_key` -- string, random SHA256 Hash hexdigest associated with
  transaction
  '''

  log(f'database.delete_transaction(): with transaction_id {transaction_id}',
      level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (transaction_id, removal_key)

  result = c.execute('''DELETE FROM transactions
                        WHERE transaction_id=? AND removal_key=?''', params)

  db_connection.commit()

  if result.rowcount:
    log('database.delete_transaction(): removed transaction_id '
        f'{transaction_id}', level='info')
  else:
    log('database.delete_transaction(): failed to remove transaction_id '
        f'{transaction_id}', level='info')

  return result.rowcount
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def safe_delete_transaction(
    transaction_id: int,
    removal_key: str,
    nfc_id: str
  ) -> int:
  '''safe variant of delete_transaction(), additional nfc_id required

  remove a row from table 'transactions' where both
  'transaction_id'=`transaction_id` AND 'removal_key'=`removal_key` AND
  'nfc_id'=`nfc_id`

  returns the number of deleted rows (0 or 1)

  arguments:
  + `transaction_id` -- integer, unique auto generated primary key
  + `removal_key` -- string, random SHA256 Hash hexdigest associated with
  transaction
  + `nfc_id` -- string, NFC ID formatted as hex string
  '''

  log('database.safe_delete_transaction(): with transaction_id '
      f'{transaction_id} from nfc_id {nfc_id}', level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (transaction_id, removal_key, nfc_id)

  result = c.execute('''DELETE FROM transactions
                      WHERE transaction_id=? AND removal_key=? AND nfc_id=?''',
                      params)

  db_connection.commit()

  if result.rowcount:
    log('database.safe_delete_transaction(): removed transaction_id '
        f'{transaction_id}', level='info')
  else:
    log('database.delete_transaction(): failed to remove transaction_id '
        f'{transaction_id}', level='info')

  return result.rowcount
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@lock_and_release
def unsafe_delete_transaction(transaction_id: int) -> int:
  '''unsafe variant of delete_transaction(), no removal_key required

  remove a row from table 'transactions' where
  'transaction_id'=`transaction_id`,
  returns the number of deleted rows (0 or 1)

  arguments:
  + `transaction_id` -- integer, unique auto generated primary key
  '''

  log('database.unsafe_delete_transaction(): with transaction_id '
      f'{transaction_id}', level='debug')

  global db_connection
  c = db_connection.cursor()

  params = (transaction_id, )

  result = c.execute('''DELETE FROM transactions
                        WHERE transaction_id=?''', params)

  db_connection.commit()

  if result.rowcount:
    log('database.unsafe_delete_transaction(): removed transaction_id '
        f'{transaction_id}', level='info')
  else:
    log('database.delete_transaction(): failed to remove transaction_id '
        f'{transaction_id}', level='info')

  return result.rowcount
# ------------------------------------------------------------------------------
# ==============================================================================
