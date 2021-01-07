"""
The latest version of this package is available at:
<http://github.com/jantman/ecsjobs>

##################################################################################
Copyright 2017 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of ecsjobs, also known as ecsjobs.

    ecsjobs is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ecsjobs is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with ecsjobs.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/ecsjobs> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##################################################################################
"""

import os
import logging
import glob
from copy import copy, deepcopy
from datetime import datetime

import yaml
import boto3

from ecsjobs.jobs import get_job_classes
from ecsjobs.schema import Schema

logger = logging.getLogger(__name__)


class Config(object):

    #: File extensions to consider as YAML config files.
    YAML_EXTNS = ['.yml', '.yaml']

    #: Default values for global configuration settings.
    _global_defaults = {
        'inter_poll_sleep_sec': 10,
        'max_total_runtime_sec': 3600,
        'email_subject': 'ECSJobs Report',
        'failure_html_path': None,
        'failure_command': None
    }

    def __init__(self):
        self.s3 = boto3.resource('s3')
        self._raw_conf = {}
        self._global_conf = {}
        self._jobs = []
        self._load_config()
        self._validate_config()
        self._make_jobs()

    @property
    def schedule_names(self):
        """
        Return a list of all String schedule names defined in the config.

        :return: all defined schedule names
        :rtype: list
        """
        return sorted(list(set([j.schedule_name for j in self._jobs])))

    def jobs_for_schedules(self, schedule_names):
        """
        Given one or more schedule names, return the list of jobs for those
        schedules (in order).

        :param schedule_names: schedule names to get jobs for
        :type schedule_names: list
        :return: list of Jobs for the specified schedules
        :rtype: list
        """
        return [j for j in self.jobs if j.schedule_name in schedule_names]

    @property
    def jobs(self):
        """
        Return the list of :py:class:`ecsjobs.jobs.base.Job` instances.

        :return: list of jobs
        :rtype: list
        """
        return copy(self._jobs)

    def get_global(self, k):
        """
        Return the value of the specified global configuration setting,
        from the global configuration (if present) or else from the global
        defaults.

        :param k: configuration key to get
        :return: value of global config setting
        """
        if k in self._global_conf:
            return self._global_conf[k]
        return self._global_defaults[k]

    def _load_config(self):
        """
        Check environment variables; call either :py:meth:`~._load_config_s3`
        or :py:meth:`~._load_config_local`.

        :raises: RuntimeError
        """
        if 'ECSJOBS_BUCKET' in os.environ and 'ECSJOBS_KEY' in os.environ:

            self._load_config_s3(
                os.environ['ECSJOBS_BUCKET'],
                os.environ['ECSJOBS_KEY']
            )
        elif 'ECSJOBS_LOCAL_CONF_PATH' in os.environ:
            self._load_config_local(os.environ['ECSJOBS_LOCAL_CONF_PATH'])
        else:
            raise RuntimeError(
                'ERROR: You must export either ECSJOBS_BUCKET and ECSJOBS_KEY, '
                'or ECSJOBS_LOCAL_CONF_PATH'
            )

    def _load_config_s3(self, bucket_name, key_name):
        """
        Retrieve and load configuration from S3. Sets ``self._raw_conf``.

        :param bucket_name: Name of the S3 bucket to retrieve config from
        :type bucket_name: str
        :param key_name: config key or prefix in bucket
        :type key_name: str
        """
        logger.debug('Loading configuration from bucket %s key/prefix %s',
                     bucket_name, key_name)
        bkt = self.s3.Bucket(bucket_name)
        if self._key_is_yaml(key_name):
            logger.info('Loading configuration from single file %s in %s',
                        key_name, bucket_name)
            self._raw_conf = self._get_yaml_from_s3(bkt, key_name)
        else:
            logger.info('Loading multi-file configuration from prefix %s in '
                        'bucket %s', key_name, bucket_name)
            self._raw_conf = self._get_multipart_config(bkt, key_name)
        logger.debug('Configuration load complete:\n%s', self._raw_conf)

    def _load_config_local(self, conf_path):
        """
        Load configuration from the local filesystem. Sets ``self._raw_conf``.

        :param conf_path: path to configuration on local FS
        :type conf_path: str
        """
        logger.debug(
            'Loading configuration from local filesystem: %s', conf_path
        )
        if not os.path.exists(conf_path):
            raise RuntimeError(
                'ERROR: Config path does not exist: %s' % conf_path
            )
        if not os.path.isdir(conf_path):
            self._raw_conf = self._load_yaml_from_disk(conf_path)
            return
        # else it's a directory; load recursively
        if not conf_path.endswith('/'):
            conf_path += '/'
        files = []
        for ext in self.YAML_EXTNS:
            files.extend(glob.glob('%s*%s' % (conf_path, ext)))
        res = {'global': {}, 'jobs': []}
        for f in sorted(files):
            if os.path.basename(f) in ['global%s' % e for e in self.YAML_EXTNS]:
                res['global'] = self._load_yaml_from_disk(f)
            else:
                res['jobs'].append(self._load_yaml_from_disk(f))
        self._raw_conf = res

    def _load_yaml_from_disk(self, path):
        """
        Load a YAML file from disk and return the contents.

        :param path: path to load from
        :type path: str
        :return: deserialized YAML file contents
        :rtype: dict
        """
        with open(path, 'r') as fh:
            return yaml.load(fh, Loader=yaml.FullLoader)

    def _key_is_yaml(self, key):
        """
        Test whether or not the specified S3 key is a YAML file.

        :param key: key in S3
        :type key: str
        :return: whether key is a YAML file
        :rtype: bool
        """
        for extn in self.YAML_EXTNS:
            if key.endswith(extn):
                return True
        return False

    def _get_multipart_config(self, bucket, prefix):
        """
        Retrieve each piece of a multipart config from S3; return the combined
        configuration (i.e. the corresponding single-dict config).

        :param bucket: the S3 bucket to retrieve configs from
        :type bucket: :py:class:`S3.Bucket <S3.Bucket>`
        :param prefix: prefix for configuration files
        :type prefix: str
        :return: combined configuration dict
        :rtype: dict
        """
        res = {'global': {}, 'jobs': []}
        for obj in sorted(
            list(bucket.objects.filter(Prefix=prefix)), key=lambda x: x.key
        ):
            fname = obj.key.replace(prefix, '')
            if not self._key_is_yaml(fname):
                continue
            body = self._get_yaml_from_s3(bucket, obj.key)
            if fname in ['global%s' % extn for extn in self.YAML_EXTNS]:
                res['global'] = body
            else:
                res['jobs'].append(body)
        return res

    def _get_yaml_from_s3(self, bucket, key):
        """
        Retrieve the contents of a file from S3 and deserialize the YAML.

        :param bucket: the S3 bucket to retrieve the file from
        :type bucket: :py:class:`S3.Bucket <S3.Bucket>`
        :param key: key/path of the file
        :type key: str
        :return: deserialized YAML file contents
        :rtype: dict
        """
        try:
            obj = bucket.Object(key)
        except Exception:
            logger.error('Unable to retrieve s3://%s/%s', bucket.name, key,
                         exc_info=True)
            raise RuntimeError(
                'ERROR: Unable to retrieve key %s from bucket %s' % (
                    bucket.name, key
                )
            )
        try:
            body = obj.get()['Body'].read()
        except Exception:
            logger.error('Unable to read s3://%s/%s', bucket.name, key,
                         exc_info=True)
            raise RuntimeError(
                'ERROR: Unable to read key %s from bucket %s' % (
                    bucket.name, key
                )
            )
        try:
            res = yaml.load(body, Loader=yaml.FullLoader)
        except Exception:
            logger.error('Unable to load YAML from s3://%s/%s', bucket.name,
                         key, exc_info=True)
            raise RuntimeError(
                'ERROR: Unable to load YAML from key %s from bucket %s' % (
                    bucket.name, key
                )
            )
        return res

    def _validate_config(self):
        """
        Validate the configuration in ``self._raw_conf``. Writes
        ``self._global_conf``.
        """
        Schema().validate(self._raw_conf)
        self._global_conf = self._raw_conf['global']
        if self._global_conf.get('failure_html_path', None) is not None:
            self._global_conf[
                'failure_html_path'
            ] = self._global_conf[
                'failure_html_path'
            ].format(date=datetime.now().strftime('%Y-%m-%dT%H-%M-%S'))

    def _make_jobs(self):
        """
        Reads ``self._jobs_conf`` and instantiates job classes, populating
        ``self._jobs``.
        """
        logger.debug('Instantiating Job classes...')
        jobclasses = get_job_classes()
        for j in self._raw_conf['jobs']:
            cls = jobclasses.get(j['class_name'], None)
            if cls is None:
                raise RuntimeError(
                    'ERROR: No known Job subclass "%s" (job %s)' % (
                        j['class_name'], j['name']
                    )
                )
            conf = deepcopy(j)
            del conf['class_name']
            self._jobs.append(cls(**conf))
        logger.info('Created %d Job instances', len(self._jobs))
