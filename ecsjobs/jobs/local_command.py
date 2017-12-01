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

import abc  # noqa
from os import unlink, fdopen, chmod
from stat import S_IRUSR, S_IWUSR, S_IXUSR
from datetime import datetime
from ecsjobs.jobs.base import Job
import logging
import subprocess
import requests
import boto3
from tempfile import mkstemp

logger = logging.getLogger(__name__)


class LocalCommand(Job):
    """
    Job class to run a local command via :py:func:`subprocess.run`. The
    :py:attr:`~.output` property of this class contains combined STDOUT and
    STDERR.
    """

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'properties': {
            'command': {
                'oneOf': [
                    {'type': 'string'},
                    {
                        'type': 'array',
                        'items': [
                            {'type': 'string'}
                        ]
                    }
                ]
            },
            'shell': {'type': 'boolean'},
            'timeout': {
                'oneOf': [
                    {'type': 'integer'},
                    {'type': 'null'}
                ]
            },
            'script_source': {
                'type': 'string',
                'format': 'url',
                'pattern': '^(s3|http|https)://.*$'
            }
        }
    }

    def __init__(self, name, schedule, summary_regex=None,
                 cron_expression=None, command=None,
                 shell=False, timeout=None, script_source=None):
        """
        :param name: unique name for this job
        :type name: str
        :param schedule: the name of the schedule this job runs on
        :type schedule: str
        :param summary_regex: A regular expression to use for extracting a
          string from the job output for use in the summary table. If there is
          more than one match, the last one will be used.
        :type summary_regex: ``string`` or ``None``
        :param cron_expression: A cron-like expression parsable by
          `cronex <https://github.com/ericpruitt/cronex>`_ specifying when the
          job should run. This has the effect of causing runs to skip this job
          unless the expression matches. It's recommended not to use any minute
          specifiers and not to use any hour specifiers if the total runtime
          of all jobs is more than an hour.
        :type cron_expression: str
        :param command: The command to execute as either a String or a List of
          Strings, as used by :py:func:`subprocess.run`. If ``script_source`` is
          specified and this parameter is not an empty string or empty list, it
          will be passed as arguments to the downloaded script.
        :type command: :py:obj:`str` or :py:obj:`list`
        :param shell: Whether or not to execute the provided command through the
          shell. Corresponds to the ``shell`` argument of
          :py:func:`subprocess.run`.
        :type shell: bool
        :param timeout: An integer number of seconds to allow the command to
          run. Cooresponds to the ``timeout`` argument of
          :py:func:`subprocess.run`.
        :type timeout: int
        :param script_source: A URL to retrieve an executable script from, in
          place of ``command``. This currently supports URLs with ``http://``,
          ``https://`` or ``s3://`` schemes. HTTP and HTTPS URLs must be
          directly retrievable without any authentication. S3 URLs will use the
          same credentials already in use for the session. **Note** that this
          setting will cause ecsjobs to download and execute code from a
          potentially untrusted location.
        :type script_source: str
        """
        super(LocalCommand, self).__init__(
            name,
            schedule,
            summary_regex=summary_regex,
            cron_expression=cron_expression
        )
        self._command = command
        self._shell = shell
        self._timeout = timeout
        self._script_source = script_source
        if command is None and script_source is None:
            raise RuntimeError(
                'LocalCommand must have either "command" or "script_source" '
                'specified.'
            )

    def run(self):
        """
        Run the command for the job. Either raise an exception or return
        True if the command exited 0, False if it exited non-zero.

        :return: True if command exited 0, False otherwise.
        """
        if self._script_source is not None:
            self._command = self._get_script(self._script_source)
        logger.debug('Job %s: Running command %s shell=%s timeout=%s',
                     self.name, self._command, self._shell, self._timeout)
        try:
            self._started = True
            self._start_time = datetime.now()
            s = subprocess.run(
                self._command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=self._shell,
                timeout=self._timeout
            )
            self._exit_code = s.returncode
            self._output = s.stdout.decode()
            logger.debug('Job %s: command finished.', self.name)
        except subprocess.TimeoutExpired as exc:
            logger.warning('LocalCommand %s timed out after %s seconds',
                           self.name, exc.timeout)
            self._output = exc.output.decode()
            raise
        finally:
            self._finished = True
            self._finish_time = datetime.now()
            if self._script_source is not None:
                if isinstance(self._command, type([])):
                    unlink(self._command[0])
                else:
                    unlink(self._command)
        return self._exit_code == 0

    def report_description(self):
        """
        Return a one-line description of the Job for use in reports.

        :rtype: str
        """
        if self._script_source is not None:
            return self._script_source
        return self._command

    def _get_script(self, script_url):
        """
        Download a script from HTTP/HTTPS or S3 to a temporary path, make it
        executable, and return the command to execute.

        :param script_url: URL to download - HTTP/HTTPS or S3
        :type script_url: str
        :return: path to the downloaded executable script if ``self._command``
          is an empty string, empty array, or None. Otherwise, a list whose
          first element is the path to the downloaded executable script, and
          then contains ``self._command``.
        :rtype: str
        """
        if script_url.startswith('s3://'):
            url = script_url[5:]
            bkt, key = url.split('/', 1)
            logger.debug(
                'Retrieving script for %s from S3; bucket=%s key=%s',
                self.name, bkt, key
            )
            s3 = boto3.client('s3')
            content = s3.get_object(
                Bucket=bkt,
                Key=key
            )['Body'].read()
            logger.debug('Got script:\n%s', content)
        elif script_url.startswith('http'):
            logger.debug('Retrieving script for %s from: %s', self.name,
                         script_url)
            content = requests.get(script_url).text
            logger.debug('Got script:\n%s', content)
        else:
            raise RuntimeError('Error: unsupported URL scheme: %s' % script_url)
        fmode = 'w'
        if isinstance(content, type(b'')):
            fmode = 'wb'
        fd, path = mkstemp('ecsjobs-%s' % self.name)
        logger.info('Writing script for %s to: %s', self.name, path)
        fh = fdopen(fd, fmode)
        fh.write(content)
        fh.close()
        chmod(path, S_IRUSR | S_IWUSR | S_IXUSR)
        if self._command == '' or self._command == [] or self._command is None:
            return path
        if isinstance(self._command, type('')):
            self._command = [self._command]
        return [path] + self._command
