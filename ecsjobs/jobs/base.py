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


class Job(object):
    """
    Base class for all Job types/classes.

    Required configuration:

    * **name** - A unique name for the job.
    * **class_name** - The name of a :py:class:`ecsjobs.jobs.base.Job` subclass.
    * **schedule** - A string to identify which jobs to run at which times.

    Plus whatever configuration items are required by subclasses.
    """

    _schema_dict = {
        'type': 'object',
        'title': 'Configuration for base Job class',
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

    def __init__(self, name, schedule, **kwargs):
        """
        Initialize a Job object.

        :param name: unique name for this job
        :type name: str
        :param schedule: the name of the schedule this job runs on
        :type schedule: str
        """
        self._name = name
        self._schedule_name = schedule
        self._started = False
        self._finished = False

    @property
    def name(self):
        """
        Return the Job Name.

        :return: Job name
        :rtype: str
        """
        return self._name

    @property
    def schedule_name(self):
        """
        Return the configured schedule name for this job.

        :return: schedule name
        :rtype: str
        """
        return self._schedule_name

    @property
    def is_started(self):
        """
        Return whether or not the Job has been started.

        :return: whether or not the Job has been started
        :rtype: bool
        """
        return self._started

    @property
    def is_finished(self):
        """
        Return whether or not the Job is finished.

        :return: whether or not the Job is finished
        :rtype: bool
        """
        return self._finished
