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
  Collection of tests for werkzeugverleih.webserver
dependencies:
  pytest
"""

import werkzeugverleih.config as cfg
import werkzeugverleih.log as log
import werkzeugverleih.database as db
import werkzeugverleih.webserver as webserver
import werkzeugverleih.nfc as nfc
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

  cfg.STREAM_FRAMERATE = 1000

  log.initialize_logger()

  cfg.DATABASE_FILE_LOCATION = ':memory:'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def client():
  webserver.app.config['TESTING'] = True
  webserver.app.config['SECRET_KEY'] = b'TEST'
  open('tests/scratch/flask.cfg', 'w').close()
  cfg.FLASK_CONFIG_LOCATION = 'tests/scratch/flask.cfg'

  cfg.DATABASE_FILE_LOCATION = ':memory:'
  db.initialize_connection()
  db.create_tables()
  db.add_user('ADMIN', 'Admin', 'istrator', 'Server')  # first user == admin
  db.add_user('USER', 'User', 'User', 'Room')

  webserver.UI_LANGUAGE = 'en'

  with webserver.app.test_client() as client:
    with webserver.app.app_context():
      yield client

  db.close_connection()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fixture_tag_id(client):
  original_get_tag_id = nfc.get_tag_id
  yield client
  nfc.get_tag_id = original_get_tag_id
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fixture_add_user(fixture_tag_id):
  original_add_user = db.add_user
  yield fixture_tag_id
  db.add_user = original_add_user
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fixture_finish_checkout(fixture_tag_id):
  original_get_jpeg = webserver.get_jpeg
  original_add_transaction = db.add_transaction
  original_delete_transaction = db.delete_transaction

  yield fixture_tag_id

  db.delete_transaction = original_delete_transaction
  webserver.get_jpeg = original_get_jpeg
  db.add_transaction = original_add_transaction
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@pytest.fixture
def fixture_get_jpeg():
  original_get_jpeg = webserver.get_jpeg
  yield
  webserver.get_jpeg = original_get_jpeg
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def mock_get_tag_id_None():
  return None


def mock_get_tag_id_Admin():
  return 'ADMIN'


def mock_get_tag_id_User():
  return 'USER'


def mock_get_tag_id_Newuser():
  return 'NEW_USER'


def mock_get_tag_id_Nonuser():
  return 'NO_USER'


def mock_get_jpeg_DATA():
  return b'DATA'


def mock_get_jpeg_None():
  return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_start_webserver():
  webserver.app.config['TESTING'] = True
  webserver.app.config['SECRET_KEY'] = b'TEST'
  open('tests/scratch/flask.cfg', 'w').close()
  cfg.FLASK_CONFIG_LOCATION = 'tests/scratch/flask.cfg'

  cfg.DATABASE_FILE_LOCATION = ':memory:'
  db.initialize_connection()
  db.create_tables()

  cfg.DEBUG = True
  cfg.UI_DEFAULT_LANGUAGE = 'en'

  # create mock of app.run()
  # we are not testing the Flask framework itself
  # and pytest will use test_client() instead anyways
  def mock_run(debug=True, use_reloader=False):
    pass

  original_run = webserver.app.run
  webserver.app.run = mock_run

  webserver.start_webserver()

  webserver.app.run = original_run

  db.close_connection()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_nfc_id(fixture_tag_id):
  client = fixture_tag_id

  # Establish HTTP connection context for Flask session object
  client.get('/', follow_redirects=False)

  nfc.get_tag_id = mock_get_tag_id_None
  n = webserver.get_nfc_id()
  assert n is None

  nfc.get_tag_id = mock_get_tag_id_Admin
  n = webserver.get_nfc_id()
  assert n == 'ADMIN'

  # Test cache session
  nfc.get_tag_id = mock_get_tag_id_None
  n = webserver.get_nfc_id()
  assert n == 'ADMIN'

  client.get('/clear-nfc-cache')
  n = webserver.get_nfc_id()
  assert n is None

  nfc.get_tag_id = mock_get_tag_id_Nonuser
  n = webserver.get_nfc_id()
  assert n == 'NO_USER'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_nfc_info(fixture_tag_id):
  client = fixture_tag_id

  # Establish HTTP connection context for Flask session object
  client.get('/', follow_redirects=False)

  nfc.get_tag_id = mock_get_tag_id_None

  webserver.UI_LANGUAGE = 'de'
  info = webserver.get_nfc_info()
  assert info == "Kein NFC tag!"

  webserver.UI_LANGUAGE = 'en'
  info = webserver.get_nfc_info()
  assert info == "No NFC tag!"

  nfc.get_tag_id = mock_get_tag_id_Nonuser

  webserver.UI_LANGUAGE = 'de'
  info = webserver.get_nfc_info()
  assert info == "Unregistrierter NFC tag"

  webserver.UI_LANGUAGE = 'en'
  info = webserver.get_nfc_info()
  assert info == "Unregistered NFC tag"

  client.get('/clear-nfc-cache')
  cfg.CURRENT_USER_TEMPLATE = '${given_name} ${surname}, ${room}'
  nfc.get_tag_id = mock_get_tag_id_Admin

  info = webserver.get_nfc_info()
  assert info == "Admin istrator, Server"
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_get_jpeg():
  '''fake test for coverage since get_jpeg is just a proxy'''
  cfg.STREAM_FRAMERATE = 1000
  cfg.DEBUG = True
  webserver.get_jpeg()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_frame_generator(fixture_get_jpeg):
  cfg.STREAM_FRAMERATE = 1000

  webserver.get_jpeg = mock_get_jpeg_DATA

  gen = webserver.frame_generator()
  assert next(gen) == b'--frame\r\nContent-Type: image/jpeg\r\n\r\nDATA\r\n'

  webserver.get_jpeg = mock_get_jpeg_None

  assert next(gen) == b'--frame\r\nContent-Type: image/jpeg\r\n\r\n\r\n'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_translate_to_UI_lang():
  d = {'de': 'DEUTSCH', 'en': 'ENGLISH'}
  webserver.UI_LANGUAGE = 'de'
  assert webserver.translate_to_UI_lang(d) == 'DEUTSCH'
  webserver.UI_LANGUAGE = 'en'
  assert webserver.translate_to_UI_lang(d) == 'ENGLISH'
  assert webserver.translate_to_UI_lang(None) == 'NO TRANSLATION FOUND'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_base64ify():
  assert webserver.base64ify(b'DATA') == 'REFUQQ=='
  assert webserver.base64ify(None) == ''
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_timestamp_to_date():
  cfg.DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
  s = webserver.timestamp_to_date(0)
  assert s == '1970-01-01 00:00:00 UTC'
  s = webserver.timestamp_to_date(None)
  assert s == 'INVALID TIMESTAMP'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_checked_if_admin():
  assert webserver.checked_if_admin(True) == 'checked'
  assert webserver.checked_if_admin(False) == ''
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_translate_ui_context_filter():
  d = {'de': 'DEUTSCH', 'en': 'ENGLISH'}
  webserver.UI_LANGUAGE = 'de'
  s0 = webserver.translate_ui_context_filter(None, d)
  s1 = webserver.translate_to_UI_lang(d)
  assert s0 == s1
  webserver.UI_LANGUAGE = 'en'
  s0 = webserver.translate_ui_context_filter(None, d)
  s1 = webserver.translate_to_UI_lang(d)
  assert s0 == s1
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_site_index(client):
  url = '/index'
  webserver.UI_LANGUAGE = 'de'
  response = client.get(url)
  assert 'Startseite'.encode() in response.data
  assert 'Aktuell ausgeliehene Werkzeuge:'.encode() in response.data
  assert ('NFC Chip auf Reader legen und einen der Buttons drücken.'.encode()
          in response.data)

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url)
  assert 'Homepage'.encode() in response.data
  assert 'Currently checked out:'.encode() in response.data
  assert ('Place NFC chip on reader and press one of the buttons.'.encode()
          in response.data)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_language_selector(client):
  url = '/language'
  webserver.UI_LANGUAGE = 'de'
  response = client.get(url)
  assert 'Sprache auswählen'.encode() in response.data

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url)
  assert 'Select language'.encode() in response.data

  response = client.get(f'{url}' '?language=de', follow_redirects=True)
  assert webserver.UI_LANGUAGE == 'de'
  assert 'Startseite'.encode() in response.data
  assert 'Aktuell ausgeliehene Werkzeuge:'.encode() in response.data
  assert ('NFC Chip auf Reader legen und einen der Buttons drücken.'.encode()
          in response.data)

  response = client.get(f'{url}' '?language=en', follow_redirects=True)
  assert webserver.UI_LANGUAGE == 'en'
  assert 'Homepage'.encode() in response.data
  assert 'Currently checked out:'.encode() in response.data
  assert ('Place NFC chip on reader and press one of the buttons.'.encode()
          in response.data)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_error_page(client):
  url = '/error'
  webserver.UI_LANGUAGE = 'de'
  response = client.get(url)
  assert 'Fehler!'.encode() in response.data
  assert '<p class="error-message">'.encode() in response.data
  assert ('Bei der gewünschten Operation ist ein Fehler aufgetreten.'.encode()
          in response.data)
  assert ('<br>Sie werden zur Startseite weitergeleitet'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=no_admin')
  assert ('NFC Chip hat nicht die benötigten Berechtigungen.'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=unknown_nfc_id')
  assert ('NFC Chip kann nicht in der Datenbank gefunden'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=fail_revert')
  assert ('letzte Ausleihe konnte nicht rückgängig gemacht werden!'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=db_integrity')
  assert ('Bei der Überprüfung der Datenbankintegrität wurde eine'.encode()
          in response.data)

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url)
  assert 'Error!'.encode() in response.data
  assert '<p class="error-message">'.encode() in response.data
  assert ('An error occured in the current operation.'.encode()
          in response.data)
  assert ('<br>You will be redirected to the homepage.'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=no_admin')
  assert ('scanned NFC chip does not have the required privileges.'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=unknown_nfc_id')
  assert ("The current NFC Chip can't be found in the database.".encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=fail_revert')
  assert ('Failed to revert the last check-out!'.encode()
          in response.data)

  response = client.get(f'{url}' '?error_type=db_integrity')
  assert ('An issue occured while checking for database integrity.'.encode()
          in response.data)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_no_nfc_tag(client):
  url = '/no-nfc-tag'
  webserver.UI_LANGUAGE = 'de'
  response = client.get(url)
  assert 'NFC Chip nicht erkannt'.encode() in response.data

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url)
  assert 'NFC Chip missing'.encode() in response.data
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_register_user(fixture_add_user):
  client = fixture_add_user
  url = '/register'

  nfc.get_tag_id = mock_get_tag_id_None
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/no-nfc-tag').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/checkout').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Nonuser

  webserver.UI_LANGUAGE = 'de'
  response = client.get(url, follow_redirects=True)
  assert 'Benutzerregistrierung'.encode() in response.data
  assert ('ist eine vorherige Registrierung notwendig.'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url, follow_redirects=True)
  assert 'User registration'.encode() in response.data
  assert ('prior user registration is required'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Newuser

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      given_name='New',
      surname='User'  # missing room parameter
    ), follow_redirects=True)
  assert 'Keine leeren Felder zulässig!'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      given_name='New',
      surname='User'  # missing room parameter
    ), follow_redirects=True)
  assert 'No empty fields permitted!'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      given_name='New',
      surname='User',
      room='NEW'
    ), follow_redirects=True)
  assert response.data == client.get('/checkout').data
  client.get('/clear-nfc-cache')

  db.delete_user('NEW_USER')

  def mock_add_user(nfc_id, given_name, surname, room):
    return False

  db.add_user = mock_add_user

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      given_name='New',
      surname='User',
      room='NEW'
    ), follow_redirects=True)
  assert 'Datenbankfehler!'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      given_name='New',
      surname='User',
      room='NEW'
    ), follow_redirects=True)
  assert 'Database error!'.encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_video_feed(client):
  response = client.get('/video-feed')
  assert 'multipart/x-mixed-replace' in response.mimetype
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_page_checkout(fixture_tag_id):
  client = fixture_tag_id
  url = '/checkout'

  nfc.get_tag_id = mock_get_tag_id_None
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/no-nfc-tag').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Nonuser
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/register').data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_finish_checkout(fixture_finish_checkout):
  client = fixture_finish_checkout
  url = '/finish-checkout'

  original_get_jpeg = webserver.get_jpeg
  webserver.get_jpeg = mock_get_jpeg_DATA

  nfc.get_tag_id = mock_get_tag_id_None
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/no-nfc-tag').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Nonuser
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/register').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Admin

  webserver.UI_LANGUAGE = 'de'
  response = client.get(url, follow_redirects=True)
  assert 'Erfolgreich ausgeliehen'.encode() in response.data
  assert 'Nicht zufrieden mit Photo?'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url, follow_redirects=True)
  assert 'Check-out successful'.encode() in response.data
  assert 'Not satisfied with photo?'.encode() in response.data
  client.get('/clear-nfc-cache')

  original_add_transaction = db.add_transaction

  def mock_add_transaction(nfc_id, image):
    original_add_transaction('NONEXISTANT_USER', image)

  db.add_transaction = mock_add_transaction

  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/error?error_type=db_integrity').data
  client.get('/clear-nfc-cache')

  def mock_add_transaction(nfc_id, image):
    return original_add_transaction('NO_USER', image)

  db.add_transaction = mock_add_transaction

  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/error?error_type=db_integrity').data
  client.get('/clear-nfc-cache')

  webserver.get_jpeg = original_get_jpeg
  db.add_transaction = original_add_transaction

  response = client.post(url, data=dict(
      transaction_id=0
    ), follow_redirects=True)
  assert response.data == client.get('/error?error_type=fail_revert').data
  client.get('/clear-nfc-cache')

  def mock_delete_transaction(transaction_id, removal_key):
    return True

  db.delete_transaction = mock_delete_transaction

  response = client.post(url, data=dict(
      transaction_id=0,
      removal_key=b'SOME_DATA'
    ), follow_redirects=True)
  assert response.data == client.get('/checkout').data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_page_checkin(fixture_tag_id):
  client = fixture_tag_id
  url = '/checkin'

  nfc.get_tag_id = mock_get_tag_id_None
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/no-nfc-tag').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Nonuser
  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/register').data
  client.get('/clear-nfc-cache')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'de'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.post(url, data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation erfolgreich'.encode() in response.data
  assert ('Werkzeuge unverzüglich wieder an ihrem ursprünglichen Platz'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'en'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.post(url, data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation successful'.encode() in response.data
  assert ('return the shown tools to their original storage location'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.post(url, data=None, follow_redirects=True)
  assert 'Werkzeuge zum Zurückgeben auswählen'.encode() in response.data
  assert ('Keine Werkzeuge zur Rückgabe vorhanden.'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.post(url, data=None, follow_redirects=True)
  assert 'Choose tools for check-in'.encode() in response.data
  assert ('Nothing to check-in.'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.get(url, follow_redirects=True)
  assert 'Werkzeuge zum Zurückgeben auswählen'.encode() in response.data
  assert ('Keine Werkzeuge zur Rückgabe vorhanden.'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  nfc.get_tag_id = mock_get_tag_id_Admin
  response = client.get(url, follow_redirects=True)
  assert 'Choose tools for check-in'.encode() in response.data
  assert ('Nothing to check-in.'.encode()
          in response.data)
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def helper_admin_privileges(client, url, method='get'):
  if method == 'post':
    client_method = client.post
  else:
    client_method = client.get

  nfc.get_tag_id = mock_get_tag_id_None
  response = client_method(url, follow_redirects=True)
  assert response.data == client.get('/no-nfc-tag').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_Nonuser
  response = client_method(url, follow_redirects=True)
  assert response.data == client.get('/register').data
  client.get('/clear-nfc-cache')

  nfc.get_tag_id = mock_get_tag_id_User
  response = client_method(url, follow_redirects=True)
  assert response.data == client.get('/error?error_type=no_admin').data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_admin_overview(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin'

  helper_admin_privileges(client, url, method='get')

  nfc.get_tag_id = mock_get_tag_id_Admin

  webserver.UI_LANGUAGE = 'de'
  response = client.get(url, follow_redirects=True)
  assert 'Admin Menü'.encode() in response.data
  assert ('Benutzer verwalten'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url, follow_redirects=True)
  assert 'Admin menu'.encode() in response.data
  assert ('Manage users'.encode()
          in response.data)
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_admin_manage_users(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/users'

  helper_admin_privileges(client, url, method='get')

  nfc.get_tag_id = mock_get_tag_id_Admin

  webserver.UI_LANGUAGE = 'de'
  response = client.get(url, follow_redirects=True)
  assert 'Admin - Benutzerverwaltung'.encode() in response.data
  assert 'Details ansehen'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url, follow_redirects=True)
  assert 'Admin - User management'.encode() in response.data
  assert 'View details'.encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_admin_manage_user(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/user'

  helper_admin_privileges(client, url, method='get')

  nfc.get_tag_id = mock_get_tag_id_Admin

  response = client.get(url, follow_redirects=True)
  assert response.data == client.get('/error?error_type=unknown_nfc_id').data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.get(f'{url}' '?nfc_id=USER', follow_redirects=True)
  assert 'Admin - Benutzerdaten ändern'.encode() in response.data
  assert 'Benutzer löschen'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(f'{url}' '?nfc_id=USER', follow_redirects=True)
  assert 'Admin - change user data'.encode() in response.data
  assert 'Delete user'.encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_change_user(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/change_user'

  helper_admin_privileges(client, url, method='post')

  nfc.get_tag_id = mock_get_tag_id_Admin

  response = client.get(url, follow_redirects=True)
  assert '405 Method Not Allowed'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'  # incomplete POST data
    ), follow_redirects=True)
  assert ("Eingabefehler! Es wurde keine Änderung durchgeführt.".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'  # incomplete POST data
    ), follow_redirects=True)
  assert ("Input error! No changes were made.".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server'
    ), follow_redirects=True)
  assert "Entziehen eigener Adminrechte verboten!".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server'
    ), follow_redirects=True)
  assert "revoke your own admin privileges!".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server',
      admin=True
    ), follow_redirects=True)
  assert "Daten geändert".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server',
      admin=True
    ), follow_redirects=True)
  assert "Data changed".encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_delete_user(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/delete_user'

  helper_admin_privileges(client, url, method='post')

  nfc.get_tag_id = mock_get_tag_id_Admin

  response = client.get(url, follow_redirects=True)
  assert '405 Method Not Allowed'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'  # incomplete POST data
    ), follow_redirects=True)
  assert ("Eingabefehler! Es wurde keine Änderung durchgeführt.".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'  # incomplete POST data
    ), follow_redirects=True)
  assert ("Input error! No changes were made.".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server'
    ), follow_redirects=True)
  assert "Löschen des eigenen Accounts verboten!".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN',
      given_name='Admin',
      surname='"istrator',
      room='Server'
    ), follow_redirects=True)
  assert "delete your own account!".encode() in response.data
  client.get('/clear-nfc-cache')

  db.add_user('TEST', 'TEST', 'TEST', 'TEST')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='TEST',
      given_name='TEST',
      surname='"TEST',
      room='TEST'
    ), follow_redirects=True)
  assert "Admin - Benutzer löschen".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='TEST',
      given_name='TEST',
      surname='"TEST',
      room='TEST'
    ), follow_redirects=True)
  assert "Admin - delete user".encode() in response.data
  client.get('/clear-nfc-cache')

  db.add_user('TEST', 'TEST', 'TEST', 'TEST')
  db.add_transaction('TEST', b'DATA')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='TEST',
      given_name='TEST',
      surname='"TEST',
      room='TEST'
    ), follow_redirects=True)
  assert ("ausstehenden Ausleihen können nicht gelöscht werden!".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='TEST',
      given_name='TEST',
      surname='"TEST',
      room='TEST'
    ), follow_redirects=True)
  assert "delete users with active check-outs!".encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_confirm_delete_user(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/confirm_delete_user'

  helper_admin_privileges(client, url, method='post')

  nfc.get_tag_id = mock_get_tag_id_Admin

  response = client.get(url, follow_redirects=True)
  assert '405 Method Not Allowed'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'
    ), follow_redirects=True)
  assert "Löschen des eigenen Accounts verboten!".encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='ADMIN'
    ), follow_redirects=True)
  assert "delete your own account!".encode() in response.data
  client.get('/clear-nfc-cache')

  db.add_user('TEST', 'TEST', 'TEST', 'TEST')

  response = client.post(url, data=dict(
      nfc_id='TEST'
    ), follow_redirects=True)
  assert response.data == client.get('/admin/users').data
  client.get('/clear-nfc-cache')

  db.add_user('TEST', 'TEST', 'TEST', 'TEST')
  db.add_transaction('TEST', b'DATA')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data=dict(
      nfc_id='TEST'
    ), follow_redirects=True)
  assert ("ausstehenden Ausleihen können nicht gelöscht werden!".encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data=dict(
      nfc_id='TEST'
    ), follow_redirects=True)
  assert "delete users with active check-outs!".encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def test_admin_manage_transactions(fixture_tag_id):
  client = fixture_tag_id
  url = '/admin/transactions'

  helper_admin_privileges(client, url, method='get')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'de'
  nfc.get_tag_id = mock_get_tag_id_Admin

  response = client.post(url, data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation erfolgreich'.encode() in response.data
  assert ('Werkzeuge unverzüglich wieder an ihrem ursprünglichen Platz'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation successful'.encode() in response.data
  assert ('return the shown tools to their original storage location'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(f'{url}' '?nfc_id=ADMIN', data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation erfolgreich'.encode() in response.data
  assert ('Werkzeuge unverzüglich wieder an ihrem ursprünglichen Platz'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  transaction_id = db.add_transaction('ADMIN', b'DATA')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(f'{url}' '?nfc_id=ADMIN', data={
      'checkin-ids': [transaction_id]
    }, follow_redirects=True)
  assert 'Operation successful'.encode() in response.data
  assert ('return the shown tools to their original storage location'.encode()
          in response.data)
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.get(url, follow_redirects=True)
  assert 'Admin - Ausleihen verwalten'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(url, follow_redirects=True)
  assert 'Admin - Checkout management'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.get(f'{url}' '?nfc_id=ADMIN', follow_redirects=True)
  assert 'Admin - Ausleihen verwalten'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.get(f'{url}' '?nfc_id=ADMIN', follow_redirects=True)
  assert 'Admin - Checkout management'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'de'
  response = client.post(url, data={
      'checkin-ids': []
    }, follow_redirects=True)
  assert 'Admin - Ausleihen verwalten'.encode() in response.data
  client.get('/clear-nfc-cache')

  webserver.UI_LANGUAGE = 'en'
  response = client.post(url, data={
      'checkin-ids': []
    }, follow_redirects=True)
  assert 'Admin - Checkout management'.encode() in response.data
  client.get('/clear-nfc-cache')
# ------------------------------------------------------------------------------
