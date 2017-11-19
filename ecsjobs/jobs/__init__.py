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

from copy import deepcopy

from ecsjobs.jobs.base import Job
from ecsjobs.jobs.ecs_task import EcsTask
from ecsjobs.jobs.docker_exec import DockerExec
from ecsjobs.jobs.ecs_docker_exec import EcsDockerExec
from ecsjobs.jobs.local_command import LocalCommand


def get_job_classes():
    jobclasses = {}
    for cls in Job.__subclasses__():
        jobclasses[cls.__name__] = cls
    return jobclasses


def schema_for_job_class(cls):
    """
    Given a :py:class:`ecsjobs.jobs.base.Job` subclass, return the final
    JSONSchema for it.

    :param cls: Class to get schema for
    :type cls: ``class``
    :return: final combined JSONSchema for the class
    :rtype: dict
    """
    s = deepcopy(cls._schema_dict)
    s['properties'].update(Job._schema_dict['properties'])
    s['required'] = sorted(list(set(
        s.get('required', []) + Job._schema_dict['required']
    )))
    s['properties']['class_name'] = {'enum': [cls.__name__]}
    s['title'] = 'Configuration for %s class instance' % cls.__name__
    return s
