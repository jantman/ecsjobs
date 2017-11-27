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
import boto3

logger = logging.getLogger(__name__)


class EcsDockerExec(Job):

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'schedule': {'type': 'string'},
            'class_name': {'type': 'string'}
        },
        'required': [
            'name',
            'schedule',
            'class_name'
        ]
    }

    def __init__(self, name, schedule, summary_regex=None,
                 cron_expression=None):
        super(EcsDockerExec, self).__init__(
            name, schedule, summary_regex=summary_regex,
            cron_expression=cron_expression
        )
        self._ecs = None
        self._docker = None

    def run(self):
        self._ecs = boto3.client('ecs')
        self._docker = docker.from_env()
        raise NotImplementedError()
