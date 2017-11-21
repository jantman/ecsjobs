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
from datetime import datetime
from ecsjobs.jobs.base import Job
import logging
import subprocess

logger = logging.getLogger(__name__)


class LocalCommand(Job):
    """
    Job class to run a local command via :py:func:`subprocess.run`. The
    :py:prop:`~.output` property of this class contains combined STDOUT and
    STDERR. If the ``timeout`` configuration option is set,
    :py:prop:`~.exitcode` will be set to -2 if a timeout occurs.
    """

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
                        ],
                        'additionalItems': False
                    }
                ]
            },
            'shell': {'type': 'boolean'},
            'timeout': {
                'oneOf': [
                    {'type': 'integer'},
                    {'type': 'null'}
                ]
            }
        },
        'required': [
            'command'
        ]
    }

    _defaults = {
        'shell': False,
        'timeout': None
    }

    def __init__(self, name, schedule, **kwargs):
        """
        Initialize a LocalCommand object.

        :param name: unique name for this job
        :type name: str
        :param schedule: the name of the schedule this job runs on
        :type schedule: str
        :param kwargs: keyword arguments; see :py:attr:`~._schema_dict`
        :type kwargs: dict
        """
        super(LocalCommand, self).__init__(name, schedule, **kwargs)

    def run(self):
        """
        Run the job.

        This method sets ``self._started``, ``self._finished``,
        ``self._start_time``, ``self._finish_time``, ``self._exit_code`` and
        ``self._output``.

        :return: True if command exited 0, False otherwise.
        """
        logger.debug('Job %s: Running command %s shell=%s timeout=%s',
                     self.name, self._config['command'], self._config['shell'],
                     self._config['timeout'])
        try:
            self._started = True
            self._start_time = datetime.now()
            s = subprocess.run(
                self._config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=self._config['shell'],
                timeout=self._config['timeout']
            )
            self._finished = True
            self._finish_time = datetime.now()
            self._exit_code = s.returncode
            self._output = s.stdout.decode()
            logger.debug('Job %s: command finished.', self.name)
        except subprocess.TimeoutExpired as exc:
            self._finished = True
            self._finish_time = datetime.now()
            logger.warning('LocalCommand %s timed out after %s seconds',
                           self.name, exc.timeout)
            self._exit_code = -2
            self._output = exc.output.decode()
        return self._exit_code == 0
