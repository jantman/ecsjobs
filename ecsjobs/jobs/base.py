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

import abc
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class Job(object):
    """
    Base class for all Job types/classes.

    Required configuration:

    * **name** - A unique name for the job.
    * **class_name** - The name of a :py:class:`ecsjobs.jobs.base.Job` subclass.
    * **schedule** - A string to identify which jobs to run at which times.

    Plus whatever configuration items are required by subclasses.
    """

    __metaclass__ = abc.ABCMeta

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

    _defaults = {}

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
        self._exit_code = -1
        self._output = None
        self._start_time = None
        self._finish_time = None
        self._config = deepcopy(self._defaults)
        self._config.update(kwargs)

    def __repr__(self):
        return '<%s name="%s">' % (type(self).__name__, self.name)

    @property
    def error_repr(self):
        """
        Return a detailed representation of the job state for use in error
        reporting.

        :return: detailed representation of job in case of error
        :rtype: str
        """
        return "%s\nSchedule Name: %s\nStarted: %s\nFinished: %s\n" \
               "Exit Code: %s\nOutput: %s\n" % (
                   self.__repr__(), self._schedule_name, self._started,
                   self._finished, self._exit_code, self._output
               )

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

    @property
    def exitcode(self):
        """
        For Job subclasses that result in a command exit code, return the
        integer exitcode. For Job subclasses that result in a boolean (success /
        failure) status, return 0 on success or 1 on failure. Returns -1 if the
        Job has not completed.

        :return: Job exit code or (0 / 1) status
        :rtype: int
        """
        return self._exit_code

    @property
    def output(self):
        """
        Return the output of the Job as a string, or None if the job has not
        completed.

        :return: Job output
        :rtype: str
        """
        return self._output

    @abc.abstractmethod
    def run(self):
        """
        Run the job.

        This method sets ``self._started`` and ``self._start_time``. If the Job
        runs synchronously, this method also sets ``self._finished``,
        ``self._exit_code``, ``self._finish_time`` and ``self._output``.

        :return: True if job finished successfully, False if job finished but
          failed, or None if the job is still running in the background.
        """
        raise NotImplementedError(
            'ERROR: Job subclass must implement run() method.'
        )

    def poll(self):
        """
        For asynchronous jobs (:py:prop:`~.is_started` is True but
        :py:prop:`~.is_finished` is False), check if the job has finished yet.
        If not, return :py:prop:`~.is_finished`. If the job has finished, update
        ``self._finish_time``, ``self._exit_code``, ``self._output`` and
        ``self._finished`` and then return :py:prop:`~.is_finished`.

        :return: :py:prop:`~.is_finished`
        :rtype: bool
        """
        return self.is_finished
