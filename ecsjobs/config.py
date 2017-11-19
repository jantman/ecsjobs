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

import logging

import yaml
import boto3

from ecsjobs.jobs import get_job_classes

logger = logging.getLogger(__name__)


class Config(object):

    YAML_EXTNS = ['.yml', '.yaml']

    def __init__(self, bucket_name, key_name):
        logger.debug('Initializing Config using bucket_name=%s key_name=%s',
                     bucket_name, key_name)
        self._bucket_name = bucket_name
        self._key_name = key_name
        self.s3 = boto3.resource('s3')
        self._raw_conf = {}
        self._global_conf = {}
        self._jobs_conf = []
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
        return sorted(list(set([j.schedule_name for j in self._jobs.values()])))

    def _load_config(self):
        """
        Retrieve and load configuration from S3. Sets ``self._raw_conf``.
        """
        logger.debug('Loading configuration from %s', self._bucket_name)
        bkt = self.s3.Bucket(self._bucket_name)
        if self._key_is_yaml(self._key_name):
            logger.info('Loading configuration from single file %s in %s',
                        self._key_name, self._bucket_name)
            self._raw_conf = self._get_yaml_from_s3(bkt, self._key_name)
        else:
            logger.info('Loading multi-file configuration from prefix %s in '
                        'bucket %s', self._key_name, self._bucket_name)
            self._raw_conf = self._get_multipart_config(bkt, self._key_name)
        logger.debug('Configuration load complete:\n%s', self._raw_conf)

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
            res = yaml.load(body)
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
        ``self._global_conf`` and ``self._jobs_conf``.
        """
        logger.warning('WARNING - Config validation not implemented!')

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
            self._jobs.append(cls(**j))
        logger.info('Created %d Job instances', len(self._jobs))
