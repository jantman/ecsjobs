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
from datetime import datetime

import docker

logger = logging.getLogger(__name__)


class DockerExecMixin(object):
    """
    Mixin class to be used in other classes for Docker Exec.
    """

    def _docker_run(self):
        """
        Run ``self._command`` in ``self._container_name``. Set class attributes
        as appropriate.
        """
        logger.debug('Connecting to Docker...')
        self._docker = docker.from_env()
        self._docker.ping()
        logger.debug('Getting Docker container %s', self._container_name)
        self._container = self._docker.containers.get(self._container_name)
        logger.debug('Got container %s', self._container.short_id)
        logger.info('Executing "%s" against container %s (%s)', self._command,
                    self._container_name, self._container.short_id)
        self._started = True
        self._start_time = datetime.now()
        try:
            e = self._docker.api.exec_create(
                self._container.id, self._command, stdout=self._stdout,
                stderr=self._stderr, tty=self._tty, privileged=self._privileged,
                user=self._user, environment=self._environment
            )
            logger.debug('Created exec instance %s on container %s; running',
                         e['Id'], self._container.short_id)
            self._output = self._docker.api.exec_start(
                e['Id'], tty=self._tty
            ).decode().strip()
            res = self._docker.api.exec_inspect(e['Id'])
            logger.debug('Exec instance finished; PID %d exited %d',
                         res['Pid'], res['ExitCode'])
            self._exit_code = res['ExitCode']
        finally:
            self._finished = True
            self._finish_time = datetime.now()
