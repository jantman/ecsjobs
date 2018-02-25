Changelog
=========

0.4.0 (2018-02-25)
------------------

* Add ``awscli`` to Docker image
* Add new global configuration options:

  * **failure_html_path** - *(optional)* a string absolute path to write the HTML email report to on disk, if sending via SES fails. If not specified, a temporary file will be used (via Python's ``tempfile.mkstemp``) and its path included in the output.
  * **failure_command** - *(optional)* Array. A command to call if sending via SES fails. This should be an array beginning with the absolute path to the executable, suitable for passing to Python's ``subprocess.Popen()``. The content of the HTML report will be passed to the process on STDIN.

0.3.0 (2017-12-01)
------------------

* Document release process
* Document how to run in ECS as a Scheduled Task
* ``LocalCommand`` - if ``script_source`` parameter is specified, instead of ignoring ``command`` send it as arguments to the downloaded script.
* ``LocalCommand`` bugfix - Handle when retrieved script_source is bytes instead of string.
* Add ``-m`` / ``--only-email-if-problems`` command line argument to allow suppressing email reports if all jobs ran successfully.
* Make report email subject configurable via ``email_subject`` global configuration option.

0.2.0 (2017-11-30)
------------------

* Initial mostly-complete release
