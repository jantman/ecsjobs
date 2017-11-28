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
from ecsjobs.jobs.base import Job
from ecsjobs.jobs.docker_exec_mixin import DockerExecMixin
import logging

logger = logging.getLogger(__name__)


class DockerExec(Job, DockerExecMixin):
    """
    Class to run a command in an existing Docker container via ``exec``.
    Captures combined STDOUT and STDERR to :py:attr:`~.output` and sets
    :py:attr:`~.exitcode` to the exit code of the command/process.
    """

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'properties': {
            'container_name': {
                'type': 'string'
            },
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
            'tty': {'type': 'boolean'},
            'stdout': {'type': 'boolean'},
            'stderr': {'type': 'boolean'},
            'privileged': {'type': 'boolean'},
            'user': {'type': 'string'},
            'environment': {
                'oneOf': [
                    {'type': 'object'},
                    {'type': 'array'}
                ]
            }
        },
        'required': [
            'container_name',
            'command'
        ]
    }

    def __init__(self, name, schedule, summary_regex=None,
                 cron_expression=None, container_name=None, command=None,
                 tty=False, stdout=True, stderr=True, privileged=False,
                 user='root', environment=None):
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
        :param container_name: The name of the Docker container to run the exec
          in. Required. This can also be a container ID, but that's much less
          useful in a scheduled job.
        :type container_name: str
        :param command: The command to execute as either a String or a List of
          Strings, as used by
          :py:meth:`docker.api.exec_api.ExecApiMixin.exec_create`.
        :type command: :py:obj:`str` or :py:obj:`list`
        :param tty: Whether or not to allocate a TTY when reading output from
          the command; passed through to
          :py:meth:`docker.api.exec_api.ExecApiMixin.exec_start`.
        :type tty: bool
        :param stdout: Whether or not to attach to/capture STDOUT. Passed
          through to :py:meth:`docker.api.exec_api.ExecApiMixin.exec_create`.
        :type stdout: bool
        :param stderr: Whether or not to attach to/capture STDERR. Passed
          through to :py:meth:`docker.api.exec_api.ExecApiMixin.exec_create`.
        :type stderr: bool
        :param privileged: Whether or not to run the command as privileged.
          Passed through to
          :py:meth:`docker.api.exec_api.ExecApiMixin.exec_create`.
        :type privileged: bool
        :param user: The username to run the command as. Default is "root".
        :type user: str
        :param environment: A dictionary or list of string environment variables
          to set. Passed through to
          :py:meth:`docker.api.exec_api.ExecApiMixin.exec_create`.
        :type environment: :py:obj:`dict` or :py:obj:`list`
        """
        super(DockerExec, self).__init__(
            name, schedule, summary_regex=summary_regex,
            cron_expression=cron_expression
        )
        self._docker = None
        assert container_name is not None, 'container_name must be specified'
        self._container_name = container_name
        assert command is not None, 'command must be specified'
        self._command = command
        self._container = None
        self._tty = tty
        self._stdout = stdout
        self._stderr = stderr
        self._privileged = privileged
        self._user = user
        self._environment = environment

    def run(self):
        """
        Run the command for the job. Either raise an exception or return
        True if the command exited 0, False if it exited non-zero.

        :return: True if command exited 0, False otherwise.
        """
        self._docker_run()
        return self._exit_code == 0

    def report_description(self):
        """
        Return a one-line description of the Job for use in reports.

        :rtype: str
        """
        return '%s: %s' % (self._container_name, self._command)

    @property
    def error_repr(self):
        """
        Return a detailed representation of the job state for use in error
        reporting.

        :return: detailed representation of job in case of error
        :rtype: str
        """
        ecode = ''
        if self._exit_code is not None:
            ecode = 'Exit Code: %s\n' % self._exit_code
        try:
            cid = 'Container ID: %s\n' % self._container.short_id
        except Exception:
            cid = ''
        return "%s\nSchedule Name: %s\nStarted: %s\nFinished: %s\n" \
               "Duration: %s\n%sContainer Name: %s\n%sTTY: %s\n" \
               "Privileged: %s\nEnvironment: %s\nOutput: %s\n" % (
                   self.__repr__(), self._schedule_name, self._started,
                   self._finished, self.duration, ecode, self._container_name,
                   cid, self._tty, self._privileged, self._environment,
                   self._output
               )
