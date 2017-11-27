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
import re
import time
from cronex import CronExpression

logger = logging.getLogger(__name__)


class Job(object):
    """
    Base class for all Job types/classes.
    """

    __metaclass__ = abc.ABCMeta

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'title': 'Configuration for base Job class',
        'properties': {
            'name': {'type': 'string'},
            'schedule': {'type': 'string'},
            'class_name': {'type': 'string'},
            'summary_regex': {'type': 'string'},
            'cron_expression': {'type': 'string'}
        },
        'required': [
            'name',
            'schedule',
            'class_name'
        ]
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
        self._name = name
        self._schedule_name = schedule
        self._started = False
        self._finished = False
        self._exit_code = None
        self._output = None
        self._start_time = None
        self._finish_time = None
        self._summary_regex = summary_regex
        self._skip_reason = None
        self._cron_expression = None
        if cron_expression is not None:
            self._cron_expression = CronExpression(cron_expression)
            if not self._cron_expression.check_trigger(
                time.gmtime(time.time())[:5]
            ):
                self._skip_reason = 'cronex: "%s"' % cron_expression

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
        ecode = ''
        if self._exit_code is not None:
            ecode = 'Exit Code: %s\n' % self._exit_code
        return "%s\nSchedule Name: %s\nStarted: %s\nFinished: %s\n" \
               "Duration: %s\n%sOutput: %s\n" % (
                   self.__repr__(), self._schedule_name, self._started,
                   self._finished, self.duration, ecode, self._output
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
    def skip(self):
        """
        Either None if the job should not be skipped, or a string reason
        describing why the Job should be skipped.

        :rtype: ``None`` or ``str``
        """
        return self._skip_reason

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

    def summary(self):
        """
        Retrieve a simple one-line summary of the Job output/status.

        :return: Job one-line summary.
        :rtype: str
        """
        if self.output is None:
            return ''
        if self._summary_regex is not None:
            res = re.findall(self._summary_regex, self.output, re.M)
            if len(res) > 0:
                return res[-1]
        lines = [x for x in self.output.split("\n") if x.strip() != '']
        if len(lines) < 1:
            return ''
        return lines[-1]

    @abc.abstractmethod
    def report_description(self):
        """
        Return a one-line description of the Job for use in reports.

        :rtype: str
        """
        raise NotImplementedError()

    @property
    def duration(self):
        """
        Return the duration/runtime of the job, or None if the job did not run.

        :return: job duration
        :rtype: ``datetime.timedelta`` or ``None``
        """
        if self._start_time is None or self._finish_time is None:
            return None
        return self._finish_time - self._start_time

    @abc.abstractmethod
    def run(self):
        """
        Run the job.

        This method sets ``self._started`` and ``self._start_time``. If the Job
        runs synchronously, this method also sets ``self._finished``,
        ``self._exit_code``, ``self._finish_time`` and ``self._output``.

        In the case of an exception, this method must still set those attributes
        as appropriate and then raise the exception.

        :return: True if job finished successfully, False if job finished but
          failed, or None if the job is still running in the background.
        """
        raise NotImplementedError(
            'ERROR: Job subclass must implement run() method.'
        )

    def poll(self):
        """
        For asynchronous jobs (:py:attr:`~.is_started` is True but
        :py:attr:`~.is_finished` is False), check if the job has finished yet.
        If not, return ``False``. If the job has finished, update
        ``self._finish_time``, ``self._exit_code``, ``self._output`` and
        ``self._finished`` and then return ``True``.

        This method should **never** raise exceptions; recoverable exceptions
        should be handled via internal retry logic on subsequent poll attempts.
        Retries should be done on the next call of this method; we never want
        to sleep during this method. Unrecoverable exceptions should set
        ``self._exit_code``, ``self._output`` and ``self._finished``.

        :return: :py:attr:`~.is_finished`
        :rtype: bool
        """
        return self.is_finished
