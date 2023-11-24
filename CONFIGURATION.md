# Configuration

All relevant global configuration variables (ALL CAPS variable names in
`werkzeugverleih/config.py` ) are exposed to easy changes via
`data/werkzeugverleih.json`.

`data/werkzeugverleih.json` is a hardcoded path and can not be changed at this
point.

This document lists detailed descriptions on use and pitfalls for some of them.

___

### `DEBUG`

Default value: `false`

Setting `DEBUG` to true changes how the application runs certain functions to
make debugging easier and faster, including:

+ Run flask webserver in debug mode and show exception stacktraces directly
in the browser window
+ Instead of real camera hardware, use a repeated sequence of images as 'fake'
camera that works on every plattform - even without connecting to a real
camera. The images can be found in `tests/res/` as `1.jpg`, `2.jpg`, and
`3.jpg`.
+ Instead of real NFC reader hardware, return the contents of a file (first line
in `tests/res/nfc.txt`) as NFC ID. See also `NFC_DEBUG_DELAY`.
+ Run the routine maintenance operation once per minute instead of once per day.

___

### `LOG_LEVEL`

Default value: `info`

Allows filtering out log messages before they are written to file.

Valid values are in order of descending importance:
+ `critical`
+ `error`
+ `warning`
+ `info`
+ `debug`

Any log message with importance **less than** `LOG_LEVEL` are quietly ignored
and will not be written to the output log file.

Invalid values will default to `info`.

For more information on logging levels, see the
[Python3 documentation on logging levels](https://docs.python.org/3/library/logging.html#logging-levels). Be aware that Werkzeugverleih expects lower case strings.

___

### `STREAM_FRAMERATE`

Default value: `30`

Refresh rate of the camera feed in Hz.

Remember that the camera's hardware has its own limitations that have to be
taken into account. See also
[Sensor Modes](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)
in the picamera documentation

___

### `UI_DEFAULT_LANGUAGE`

Default value: `en`

Determines the default language setting of the webserver on first start.

___

### `NFC_DEBUG_DELAY`

Default value: `2`

Time in seconds the fake debug NFC reader should spend sleeping before
returning a fake NFC ID for the purpose of simulating the time it takes to scan
a real NFC tag on real hardware.

___

### `KEEP_BACKUPS_FOR_X_DAYS`

Default value: `2`

Number of days in the past that old database backups are kept before they are 
included in the daily removal routine. 

Be aware that a value of `2` means, it will always keep today's backup, and the
backup files with dates of the prior 2 days and remove the rest, i.e. the files
with dates of today, yesterday and the day before yesterday.

___

### `KEEP_LOGS_FOR_X_DAYS`

Default value: `14`

Number of days in the past that old logfiles are kept before they are 
included in the daily removal routine. 

Just like `KEEP_BACKUPS_FOR_X_DAYS`, it will mark today's file and the files
with dates of the prior 14 (if default) days as valid and will delete the rest.

___

### `INACTIVITY_LIMIT_DAYS`

Default value: `180`

Number of days user accounts are kept after they last accessed the system 
(their `last_access` database record was updated)

User accounts with `last_access` record older than 180 (if default) days in
the past will be removed during the next daily routine maintenance operation.

___

### `FLASK_CONFIG_LOCATION`

Default value: `data/flask.cfg`

File location of the flask configuration file, where the webserver SECRET_KEY
for session encryption is stored.

The file will be created by the application itself if it's missing, provided
the string is a valid path to a filename in an existing directory.

___

### `DATABASE_FILE_LOCATION`

Default value: `data/werkzeugverleih.db`

File location of the sqlite3 database file.

The file will be created by the application itself if it's missing, provided
the string is a valid path to a filename in an existing directory.

___

### `LOG_FILENAME_TEMPLATE`

Default value: `log_${date}.log`

Filename template for log files.

`${date}` will be automatically replaced by a date with format `DATE_FORMAT`.

___

### `LOG_FILEPATH_TEMPLATE`

Default value: `data/logs/${filename}`

Filepath template for log files. Must point to an existing directory.

`${filename}` will be automatically replaced by a filename generated with
template `LOG_FILENAME_TEMPLATE`.

___

### `BACKUP_FILENAME_TEMPLATE`

Default value: `backup_${date}.db`

Filename template for database backup files.

`${date}` will be automatically replaced by a date with format `DATE_FORMAT`.

___

### `BACKUP_FILEPATH_TEMPLATE`

Default value: `data/db_backups/${filename}`

Filepath template for database backup files. 
Must point to an existing directory.

`${filename}` will be automatically replaced by a filename generated with
template `BACKUP_FILENAME_TEMPLATE`.

___

### `CURRENT_USER_TEMPLATE`

Default value: `${given_name} ${surname}, ${room}`

Template on how to display user information.

`${given_name}`, `${surname}`, and `${room}` will be automatically replaced
with database records `given_name`, `surname`, and `room` from table `users`.

Used to display the currently active user and the user information of checked
out tools.

___

### `DATE_FORMAT`

Default value: `%Y-%m-%d`

String format for daily generated files (logs, backups).

See [strftime formatting conventions](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)

Recommended to keep in hierarchical order (Biggest to Smallest) for correct
sorting.

___

### `DATETIME_FORMAT`

Default value: `%Y-%m-%d %H:%M:%S UTC`

String format for timestamps displayed on webserver pages.
Timestamps are always UTC without any daylight savings time correction.

See [strftime formatting conventions](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)

Recommended to keep in hierarchical order (Biggest to Smallest) for correct
sorting.

___

### `LOGGING_DATETIME_FORMAT`

Default value: `%Y-%m-%d %H:%M:%S UTC`

String format for timestamps in log files.
Timestamps are always UTC without any daylight savings time correction.

See [strftime formatting conventions](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)

Recommended to keep in hierarchical order (Biggest to Smallest) for correct
sorting.

___

### `LOGGING_FORMAT`

Default value: `%(asctime)s | %(levelname)s | %(message)s`

String format for log lines.

See [LogRecord attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes)

___
