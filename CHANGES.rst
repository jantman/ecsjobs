Changelog
=========

Unreleased Changes
------------------

* Add ``awscli`` to Docker image

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
