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
import logging
import docker

logger = logging.getLogger(__name__)


class DockerExec(Job):
    """
    Class to run a command in an existing Docker container via ``exec``.
    Captures combined STDOUT and STDERR to :py:attr:`~.output` and sets
    :py:attr:`~.exitcode` to the exit code of the command/process.
    """

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'properties': {},
        'required': []
    }

    def __init__(self, name, schedule, summary_regex=None,
                 cron_expression=None):
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
        """
        super(DockerExec, self).__init__(
            name, schedule, summary_regex=summary_regex,
            cron_expression=cron_expression
        )
        self._docker = None

    def run(self):
        self._docker = docker.from_env()
        raise NotImplementedError()
