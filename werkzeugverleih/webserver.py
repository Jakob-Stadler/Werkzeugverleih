"""
name:
  Werkzeugverleih Webserver
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Core component of the package.
  Defines the application behavior when accessing pre-defined URLs
dependencies:
  flask
"""


# intra-package imports --------------------------------------------------------
import sys
import werkzeugverleih.config as cfg
import werkzeugverleih.database as db
import werkzeugverleih.camera as cam
import werkzeugverleih.nfc as nfc
from werkzeugverleih.log import log
from werkzeugverleih.template_string import (
        current_user as template_current_user )
# ------------------------------------------------------------------------------


# shared imports ---------------------------------------------------------------
from flask import (
                    Flask,
                    redirect,
                    render_template,
                    request,
                    Response,
                    session,
                    url_for
                  )
# ------------------------------------------------------------------------------


from typing import Any

# global Flask app
app = Flask('werkzeugverleih')

# current UI language
UI_LANGUAGE = cfg.UI_DEFAULT_LANGUAGE

# Initialization ---------------------------------------------------------------
from os.path import abspath
def start_webserver() -> None:
  '''start the Flask webserver'''
  flask_config_file = abspath(cfg.FLASK_CONFIG_LOCATION)

  log('webserver.start_webserver() Loading Flask config from '
      f'"{flask_config_file}"', level='info')

  app.config.from_pyfile(flask_config_file)

  global UI_LANGUAGE
  UI_LANGUAGE = cfg.UI_DEFAULT_LANGUAGE

  app.run(debug=cfg.DEBUG, use_reloader=False)
# ------------------------------------------------------------------------------


# HELPER FUNCTIONS =============================================================
# ------------------------------------------------------------------------------
def get_nfc_id() -> str:
  '''get nfc_id from cache, alternatively from hardware, cache result'''
  nfc_id = session.get('nfc_id')
  if nfc_id is None:
    nfc_id = nfc.get_tag_id()
    session['nfc_id'] = nfc_id
  else:
    log(f'webserver.get_nfc_id(): get nfc_id {nfc_id} from session cache',
        level='debug')
  return nfc_id
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def clear_nfc_cache() -> None:
  '''remove nfc_id from session to clear cached value'''
  session['nfc_id'] = None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_nfc_info() -> str:
  '''Find info about currently used nfc id and return as string'''
  nfc_id = get_nfc_id()

  if nfc_id is None:
    log('webserver.get_nfc_info(): no nfc_id detected', level='debug')
    return translate_to_UI_lang({
        'de': "Kein NFC tag!",
        'en': "No NFC tag!"
      })

  user = db.get_user(nfc_id)
  if user is None:
    log(f'webserver.get_nfc_info(): nfc_id {nfc_id} not in database',
        level='debug')
    return translate_to_UI_lang({
        'de': "Unregistrierter NFC tag",
        'en': "Unregistered NFC tag"
      })

  # return string based on template cfg.CURRENT_USER_TEMPLATE
  log(f'webserver.get_nfc_info(): returned user with nfc_id {nfc_id}',
        level='debug')
  return current_user(user)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_jpeg() -> bytes:
  '''proxy call for frame_generator(), allows function override for testing'''
  return cam.get_jpeg()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
import time
def frame_generator() -> bytes:
  '''get images from camera and prepare for motion jpeg video stream'''
  while True:
    frame = get_jpeg()
    if frame is None:
      frame = b''
    yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    time.sleep(1 / cfg.STREAM_FRAMERATE)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def translate_to_UI_lang(multilang_dict: dict) -> str:
  '''choose the correct transaltion according to UI_LANGUAGE, default to "en"'''
  try:
    return multilang_dict.get(UI_LANGUAGE,
                              multilang_dict.get('en', 'NO TRANSLATION FOUND'))
  except AttributeError:
    return 'NO TRANSLATION FOUND'
# ==============================================================================


# JINJA TEMPLATE FILERS ========================================================
# ------------------------------------------------------------------------------
from base64 import b64encode
@app.template_filter('base64')
def base64ify(image_blob: bytes) -> str:
  '''transform binary data into a base64 string

  arguments:
  + `image_blob` -- binary data, e.g. b'DATA'
  '''
  try:
    return b64encode(image_blob).decode("utf-8")
  except TypeError:
    log('webserver.base64ify(): invalid type for image_blob', level='warning')
    return ''
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from datetime import datetime
@app.template_filter('ts2date')
def timestamp_to_date(timestamp: int) -> str:
  '''format a integer unix timestamp into a human readable date

  arguments:
  + `timestamp` -- integer, seconds since Unix epoch (1970-01-01 00:00:00 UTC)
  '''
  try:
    return datetime.utcfromtimestamp(timestamp).strftime(cfg.DATETIME_FORMAT)
  except TypeError:
    return 'INVALID TIMESTAMP'
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.template_filter('is_admin')
def checked_if_admin(admin: int) -> str:
  '''return 'checked' if `admin` is true

  arguments:
  + `admin` -- integer (pseudo-bool 1 or 0), output from users table
  '''
  return 'checked' if admin else ''
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.template_filter('format_user')
def current_user(user: dict) -> str:
  '''Template string builder as Jinja template filter'''
  return template_current_user(user)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
from jinja2 import contextfilter
@app.template_filter('translate_ui')
@contextfilter
def translate_ui_context_filter(
    context: Any,
    multilang_dict: dict
  ) -> str:
  '''Jinja contextfilter to prevent caching translations'''
  return translate_to_UI_lang(multilang_dict)
# ------------------------------------------------------------------------------
# ==============================================================================


# FLASK ROUTES =================================================================
# ------------------------------------------------------------------------------
@app.route('/')
def redirect_to_index() -> Response:
  '''redirect to /index'''
  log('webserver/: redirect to index', level='debug')
  return redirect(url_for('site_index'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/index')
def site_index() -> Response:
  '''serve index page'''
  # remove cached nfc_id
  clear_nfc_cache()

  log('webserver/index: clear session and display all current transactions',
      level='info')

  nfc_info = translate_to_UI_lang({
    'de': "NFC Chip auf Reader legen und einen der Buttons drücken.",
    'en': "Place NFC chip on reader and press one of the buttons."
  })

  # get all images and display them in a picture gallery
  transaction_list = db.get_transactions()

  nfc_id_list = list({t.get('nfc_id') for t in transaction_list})

  user_dict = {u.get('nfc_id'): u
                for u in db.get_users()
                if u.get('nfc_id') in nfc_id_list }

  return render_template("index.html", nfc_info=nfc_info,
                          transaction_list=transaction_list,
                          user_dict=user_dict)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/clear-nfc-cache')
def http_clear_nfc_cache() -> Response:
  clear_nfc_cache()
  return '200 OK', 200
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/language')
def language_selector() -> Response:
  '''serve language selection page'''
  # language from /language?language=<parameter>
  language_code = request.args.get('language', default=None)

  valid_languages = ['de', 'en']
  if language_code in valid_languages:
    global UI_LANGUAGE
    UI_LANGUAGE = language_code
    return redirect(url_for('site_index'))

  return render_template("select_language.html")
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/error')
def error_page() -> Response:
  '''serve error page

  HTTP URL arguments:
  + `error_type` from /error?error_type=`parameter`
  '''
  # error_type from /error?error_type=<parameter>
  error_type = request.args.get('error_type', default=None)

  message_dict = {
    None: translate_to_UI_lang({
      'de': 'Bei der gewünschten Operation ist ein Fehler aufgetreten.',
      'en': 'An error occured in the current operation.'
    }),
    'no_admin': translate_to_UI_lang({
      'de': 'Der aufgelegte NFC Chip hat nicht die benötigten Berechtigungen.',
      'en': 'The scanned NFC chip does not have the required privileges.'
    }),
    'unknown_nfc_id': translate_to_UI_lang({
      'de': 'Der aktuelle NFC Chip kann nicht in der Datenbank gefunden '
            'werden.',
      'en': "The current NFC Chip can't be found in the database."
    }),
    'fail_revert': translate_to_UI_lang({
      'de': 'Die letzte Ausleihe konnte nicht rückgängig gemacht werden!<br>'
            'Bitte probieren Sie das entsprechende Photo mit der Funktion '
            '"Zurückgeben" zu löschen.<br>'
            'Falls dies auch nicht hilft, wenden Sie sich an die für das '
            'Werkzeuglager verantwortlichen Personen.',
      'en': 'Failed to revert the last check-out!<br>'
            'Please try to return the corresponding image with the '
            '"check-in" feature.<br>'
            'If the problem persists, please contact the people responsible '
            'for the storage room.'
    }),
    'db_integrity': translate_to_UI_lang({
      'de': 'Bei der Überprüfung der Datenbankintegrität wurde eine '
            'Unstimmigkeit festgestellt.<br>'
            'Es kann sein, dass Datensätze nicht korrekt hinzugefügt bzw. '
            'gelöscht wurden.',
      'en': 'An issue occured while checking for database integrity.<br>'
            'Some records may not have been added/removed correctly.'
    })
  }

  error_message = message_dict.get(error_type, message_dict.get(None, ''))

  error_message += translate_to_UI_lang({
      'de': '<br>Sie werden zur Startseite weitergeleitet',
      'en': '<br>You will be redirected to the homepage.'
    })

  log(f'webserver/error: display error page with type {error_type}',
      level='error')

  return render_template('error.html', nfc_info=None,
                          error_message=error_message)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/no-nfc-tag')
def no_nfc_tag() -> Response:
  '''display explanation on how to correctly scan NFC tag'''

  # see in log how many times users fail to properly scan their NFC tag
  log('webserver/no-nfc-tag: required NFC tag missing', level='info')

  return render_template("nfc_missing.html", nfc_info=None)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/register',  methods=('GET', 'POST'))
def register_user() -> Response:
  '''display the registration page for unknown NFC IDs'''
  nfc_id = get_nfc_id()
  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  # nfc_id already in db -> redirect to checkout
  if db.get_user(nfc_id) is not None:
    log('webserver/register: registered user visited registration page',
        level='info')
    return redirect(url_for('page_checkout'))

  if request.method == 'POST':
    given_name = request.form.get('given_name')
    surname = request.form.get('surname')
    room = request.form.get('room')

    # check for empty variables
    if any(n in [nfc_id, given_name, surname, room] for n in ['', None]):
      log('webserver/register: invalid data in POST request', level='warning')
      # render same page with error message
      error_message = translate_to_UI_lang({
          'de': 'Keine leeren Felder zulässig!',
          'en': 'No empty fields permitted!'
        })
      return render_template("register.html", nfc_info=get_nfc_info(),
                              error_message=error_message)

    insert_successful = db.add_user(nfc_id, given_name, surname, room)

    if insert_successful:

      log('webserver/register: successfully registered user '
            'with nfc_id {nfc_id}', level='info')

      return redirect(url_for('page_checkout'))

    else:

      log(f'webserver/register: failed to register user with nfc_id {nfc_id}',
          level='warning')

      # render same page with error message
      error_message = translate_to_UI_lang({
          'de': 'Datenbankfehler!',
          'en': 'Database error!'
        })
      return render_template("register.html", nfc_info=get_nfc_info(),
                              error_message=error_message)

    # endof: if request.method == 'POST':

  log(f'webserver/register: display registration page for nfc_id {nfc_id}',
      level='info')

  return render_template("register.html", nfc_info=get_nfc_info(),
                          error_message=None,
                          INACTIVITY_LIMIT_DAYS=cfg.INACTIVITY_LIMIT_DAYS)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/video-feed')
def video_feed() -> Response:
  '''return motion jpeg video stream'''
  # no logging since messages would be added STREAM_FRAMERATE times per seconds
  return Response(frame_generator(),
                  mimetype='multipart/x-mixed-replace; boundary=frame')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/checkout')
def page_checkout() -> Response:
  '''display live video stream of camera for checkout'''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  # nfc not in database -> registration required
  if db.get_user(nfc_id) is None:
    return redirect(url_for('register_user'))

  return render_template("checkout.html", nfc_info=get_nfc_info())
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/finish-checkout',  methods=('GET', 'POST'))
def finish_checkout() -> Response:
  '''take picture, add to database, display result'''
  # POST -> retry
  if request.method == 'POST':
    transaction_id = request.form.get('transaction_id')
    # removal key from POST arguments to prevent unintentional deletions
    removal_key = request.form.get('removal_key')

    result = db.delete_transaction(transaction_id, removal_key)

    if result:
      log(f'webserver/finish-checkout: revert transaction {transaction_id}',
            level='info')
      return redirect(url_for('page_checkout'))

    else:
      log('webserver/finish-checkout: failed to revert transaction '
          f'{transaction_id}', level='warn')
      return redirect(url_for('error_page', error_type='fail_revert'))

    # endof: if request.method == 'POST'

  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  # nfc not in database -> registration required
  if db.get_user(nfc_id) is None:
    return redirect(url_for('register_user'))

  # get image data from camera
  image = get_jpeg()

  # add transaction to database
  transaction_id = db.add_transaction(nfc_id, image)

  try:
    transaction = db.get_transaction(transaction_id)
    transaction_nfc_id = transaction.get('nfc_id')
    user = db.get_user(transaction_nfc_id)
  except AttributeError:
    # ERROR! database integrity in danger
    return redirect(url_for('error_page', error_type='db_integrity'))

  if transaction_id is None or transaction_nfc_id != nfc_id or user is None:
    # ERROR! database integrity in danger
    return redirect(url_for('error_page', error_type='db_integrity'))

  log(f'webserver/finish-checkout: added transaction {transaction_id} by '
      f'nfc_id {nfc_id}',
        level='info')

  return render_template("finish_checkout.html", nfc_info=get_nfc_info(),
                          transaction=transaction, user=user)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/checkin',  methods=('GET', 'POST'))
def page_checkin() -> Response:
  '''display content based on request method:

  + GET: display images connected to nfc id, allow selection for checkin
  + POST: remove selected images from database, display result
  '''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  # nfc not in database -> registration required
  if db.get_user(nfc_id) is None:
    return redirect(url_for('register_user'))

  if request.method == 'POST':
    # POST -> delete transactions with ids from checkin-ids argument

    # transaction ids of selected images
    id_list = request.form.getlist('checkin-ids')

    count = 0
    transaction_list = []

    for transaction_id in id_list:
      # store transaction data in list...
      transaction = db.get_transaction(transaction_id)
      transaction_list.append(transaction)
      # ...and remove from database
      removal_key = transaction.get('removal_key')
      count += db.safe_delete_transaction(transaction_id, removal_key, nfc_id)

    # format message depending on number of removed transactions
    if count > 0:
      fcount = translate_to_UI_lang({
        'de': f'{count} ' +
              ('Eintrag wurde' if count == 1 else 'Einträge wurden') +
              ' erfolgreich aus der Datenbank entfernt.',
        'en': f'{count} ' +
              ('entry' if count == 1 else 'entries') +
              ' successfully removed from the database.'
      })

      id_list = [t.get('transaction_id') for t in transaction_list]
      log(f'webserver/checkin: for nfc_id {nfc_id} '
          f'removed transactions {id_list}', level='info')

      # display results page with all removed images, allowing the user
      # to take another look at all the items he has to return to their
      # designated place
      return render_template('checkin_successful.html', nfc_info=get_nfc_info(),
                              fcount=fcount, transaction_list=transaction_list,
                              admin=False)

    # else -> Fallthrough: Render the whole page again

  transaction_list = db.get_transactions_from_nfc_id(nfc_id)

  id_list = [t.get('transaction_id') for t in transaction_list]
  log(f'webserver/checkin: for nfc_id {nfc_id} display transactions {id_list}',
      level='info')

  return render_template('checkin.html', nfc_info=get_nfc_info(),
                          transaction_list=transaction_list)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin')
def admin_overview() -> Response:
  '''display basic menu for admin users'''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  log(f'webserver/admin: access admin menu by nfc_id {nfc_id}', level='info')

  return render_template('admin_overview.html', nfc_info=get_nfc_info())
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/users')
def admin_manage_users() -> Response:
  '''display table of all users'''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  userlist = db.get_users()

  # extend dicts in userlist with number of transactions per user
  for user in userlist:
    user['transactions'] = len(
      db.get_transactions_from_nfc_id(user.get('nfc_id')))

  log(f'webserver/admin/users: display userlist with {len(userlist)} entries',
      level='info')

  return render_template('manage_users.html', nfc_info=get_nfc_info(),
                          userlist=userlist)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/user')
def admin_manage_user() -> Response:
  '''display data of a single user and allow changes/removal'''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  # error_type from /error?type=<parameter>
  error_type = request.args.get('error_type', default=None)

  error_dict = {
    'input_error': translate_to_UI_lang({
      'de': "Eingabefehler! Es wurde keine Änderung durchgeführt.",
      'en': "Input error! No changes were made."
    }),
    'demotion_error': translate_to_UI_lang({
      'de': "Entziehen eigener Adminrechte verboten!",
      'en': "Can't revoke your own admin privileges!"
    }),
    'self_deletion_error': translate_to_UI_lang({
      'de': "Löschen des eigenen Accounts verboten!",
      'en': "Can't delete your own account!"
    }),
    'transactions_remain_error': translate_to_UI_lang({
      'de': "Benutzer mit ausstehenden Ausleihen können nicht gelöscht werden!",
      'en': "Can't delete users with active check-outs!"
    }),
    'data_changed': translate_to_UI_lang({
      'de': "Daten geändert",
      'en': "Data changed"
    })  # not an error, but same functionality
  }
  display_message = error_dict.get(error_type, None)

  # user_nfc_id from /admin/user?nfc_id=<parameter>
  user_nfc_id = request.args.get('nfc_id', default=None)

  edit_user = db.get_user(user_nfc_id)

  if edit_user is None:
    return redirect(url_for('error_page', error_type='unknown_nfc_id'))

  log(f'webserver/admin/user: display user page of nfc_id {user_nfc_id} with '
      f'error_type {error_type}', level='info')

  return render_template('manage_user.html', nfc_info=get_nfc_info(),
                          user=edit_user, display_message=display_message)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/change_user',  methods=('POST', ))
def change_user() -> Response:
  '''change user data in database, POST only'''

  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  user_nfc_id = request.form.get('nfc_id')
  given_name = request.form.get('given_name')
  surname = request.form.get('surname')
  room = request.form.get('room')
  admin = 'admin' in request.form

  # check for empty variables
  if any(n in [user_nfc_id, given_name, surname, room, admin]
          for n in ['', None]):
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='input_error'))

  if user_nfc_id == nfc_id and admin != user.get('admin'):
    # admins can't take their own admin privileges!
    log(f'webserver/admin/change_user: {nfc_id} got denied taking their own '
          'admin privileges', level='info')
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='demotion_error'))

  db.update_user(user_nfc_id, given_name, surname, room, admin)

  log(f'webserver/admin/change_user: {nfc_id} updated user data for '
      f'{user_nfc_id}', level='info')

  return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                            error_type='data_changed'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/delete_user',  methods=('POST', ))
def delete_user() -> Response:
  '''remove user data from database, POST only'''

  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  user_nfc_id = request.form.get('nfc_id')
  given_name = request.form.get('given_name')
  surname = request.form.get('surname')
  room = request.form.get('room')

  # check for empty variables
  if any(n in [user_nfc_id, given_name, surname, room]
          for n in ['', None]):
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='input_error'))

  if user_nfc_id == nfc_id:
    # admins can't delete their own account
    log(f'webserver/admin/delete_user: admin {nfc_id} got denied deleting '
          'their own account', level='info')
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='self_deletion_error'))

  if len(db.get_transactions_from_nfc_id(user_nfc_id)) > 0:
    # can't delete accounts with remaining transactions
    log(f"webserver/admin/delete_user: nfc_id {user_nfc_id} has "
        "transactions remaining and can't be deleted", level='info')
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='transactions_remain_error'))

  edit_user = {
    'nfc_id':     user_nfc_id,
    'given_name': given_name,
    'surname':    surname,
    'room':       room
  }

  log(f'webserver/admin/delete_user: nfc_id {nfc_id} starting deletion '
      f'process for user with nfc_id {nfc_id}', level='info')

  return render_template('delete_user.html', nfc_info=get_nfc_info(),
                          user=edit_user)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/confirm_delete_user',  methods=('POST', ))
def confirm_delete_user() -> Response:
  '''confirmation page for user removal, POST only'''

  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  user_nfc_id = request.form.get('nfc_id')

  if user_nfc_id == nfc_id:
    # admins can't delete their own account
    log(f'webserver/admin/confirm_delete_user: admin {nfc_id} got denied '
          'deleting their own account', level='info')
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='self_deletion_error'))

  if len(db.get_transactions_from_nfc_id(user_nfc_id)) > 0:
    # can't delete accounts with remaining transactions
    log(f"webserver/admin/confirm_delete_user: nfc_id {user_nfc_id} has "
        "transactions remaining and can't be deleted", level='info')
    return redirect(url_for('admin_manage_user', nfc_id=user_nfc_id,
                              error_type='transactions_remain_error'))

  db.delete_user(user_nfc_id)

  log(f'webserver/admin/confirm_delete_user: nfc_id {nfc_id} confirmed '
      f'deletion of user with nfc_id {nfc_id}', level='info')

  return redirect(url_for('admin_manage_users'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@app.route('/admin/transactions',  methods=('GET', 'POST'))
def admin_manage_transactions() -> Response:
  '''admin equivalent of the normal checkin page

  displays all transactions from every user by default,
  allows limiting the output to a specific user by using ?nfc_id=`parameter`
  '''
  nfc_id = get_nfc_id()

  # no nfc tag -> redirect to explanation
  if nfc_id is None:
    return redirect(url_for('no_nfc_tag'))

  user = db.get_user(nfc_id)
  # nfc not in database -> registration required
  if user is None:
    return redirect(url_for('register_user'))

  if not user.get('admin'):
    # ERROR! user is not admin
    log(f'webserver/admin/*: nfc_id {nfc_id} tried to access admin page '
          'without admin privileges', level='warning')
    return redirect(url_for('error_page', error_type='no_admin'))

  # limit_to_nfc_id from /admin/transactions?nfc_id=<parameter>
  limit_to_nfc_id = request.args.get('nfc_id', default=None)

  if request.method == 'POST':

    # transaction ids of selected images
    id_list = request.form.getlist('checkin-ids')
    transaction_list = []

    count = 0
    for transaction_id in id_list:
      # store transaction data in list and remove from database
      transaction = db.get_transaction(transaction_id)
      transaction_list.append(transaction)
      count += db.unsafe_delete_transaction(transaction_id)

    # format message depending on number of removed transactions
    if count > 0:
      fcount = str(count) + ' ' + (
        'Eintrag wurde' if count == 1 else 'Einträge wurden')

      id_list = [t.get('transaction_id') for t in transaction_list]
      if limit_to_nfc_id:
        log(f'admin/transactions: for nfc_id {limit_to_nfc_id} removed '
            f'transactions {id_list}',
              level='info')
      else:
        log(f'admin/transactions: removed transactions {id_list}',
              level='info')

      # display results page with all removed images, allowing the user
      # to take another look at all the items he has to return to their
      # designated place
      return render_template('checkin_successful.html', nfc_info=get_nfc_info(),
                              fcount=fcount, transaction_list=transaction_list,
                              admin=True)

      # else -> Fallthrough: Render the whole page again
    # endof: if request.method == 'POST'

  if limit_to_nfc_id:
    transaction_list = db.get_transactions_from_nfc_id(limit_to_nfc_id)
  else:
    transaction_list = db.get_transactions()

  nfc_id_list = list({t.get('nfc_id') for t in transaction_list})

  user_dict = {u.get('nfc_id'): u
                for u in db.get_users()
                if u.get('nfc_id') in nfc_id_list }

  id_list = [t.get('transaction_id') for t in transaction_list]
  log(f'admin/transactions: for nfc_id {limit_to_nfc_id} serve list {id_list}',
        level='info')

  return render_template('manage_transactions.html', nfc_info=get_nfc_info(),
                          transaction_list=transaction_list,
                          user_dict=user_dict)
# ------------------------------------------------------------------------------
# ==============================================================================
