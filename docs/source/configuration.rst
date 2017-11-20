Configuration
=============

ecsjobs is configured via YAML files stored in S3 or locally. The paths to these files are specified via environment variables.

S3 Configuration
----------------

S3 is used as the source for the configuration files when the ``ECSJOBS_BUCKET`` and ``ECSJOBS_KEY`` environment variables are set. The former specifies the name
of the S3 bucket that configuration will be retrieved from. The latter specifies the name of
a key within the bucket to retrieve the configuration files from. If the key name ends in
``.yaml`` or ``.yml`` it will be assumed to be a file, and used as a single configuration
file. If it does not, it will be assumed to be a "directory", and all ``.yml`` or ``.yaml``
files directly below it will be used.

Local File Configuration
------------------------

Local file configuration is controlled via the ``ECSJOBS_LOCAL_CONF_PATH`` environment variable. While it's recommended to use S3 for production use, local file configuration is useful in testing or to validate config files before uploading them to S3. the ``ECSJOBS_BUCKET`` and ``ECSJOBS_KEY`` environment variables take precedence over ``ECSJOBS_LOCAL_CONF_PATH``. If the path specified by this variable is a directory, all ``.yml`` and ``.yaml`` files under it (recursively) will be loaded as configuration. Otherwise, it will be assumed to be a single YAML file.

Single File
-----------

If configuring with a single file (``ECSJOBS_KEY`` ends in ``.yml`` or ``.yaml`` and is a
file), the top-level of a file must be a mapping with keys ``global`` and ``jobs``. The
value of ``global`` must be a mapping following the schema described below. The value of
``jobs`` must be a list of mappings, each following the schema described below.

For single file configurations, Jobs within a Schedule will be executed in the order they
appear in the ``jobs`` array.

Multiple Files
--------------

If configuring with multiple files (``ECSJOBS_KEY`` does not end in ``.yml`` or ``.yaml``
and is used as a prefix/directory), all ``.yml`` or ``.yaml`` keys in the bucket beginning
with (prefixed by) ``ECSJOBS_KEY`` will be used for configuration. There must be one file
named ``global.yml`` or ``global.yaml`` corresponding to the global schema described below.
All other ``.yml`` or ``.yaml`` files will be treated as job configurations, one job per
file, each corresponding to the schema described below.

For multi-file configurations, Jobs within a Schedule will be executed in the lexicographic order of the files each Job is defined in.

Global Schema
-------------

The global configuration file or mapping should match the following:

* **from_email** - String, email address to set as FROM.
* **to_email** - List of Strings, email notification recipients.

Job Schema
----------

Each job configuration file or mapping should match the following:

* **name** - A unique name for the job.
* **class_name** - The name of a :py:class:`ecsjobs.jobs.base.Job` subclass.
* **schedule** - A string to identify which jobs to run at which times.

The rest of the Job keys depend on the class. See the documentation of each
Job subclass for the required configuration.