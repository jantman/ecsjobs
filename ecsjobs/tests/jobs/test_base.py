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

import pytest
from ecsjobs.jobs.base import Job
from datetime import datetime, timedelta


class TestBaseJob(object):

    def setup(self):
        self.cls = Job('jname', 'schedname')

    def test_init(self):
        cls = Job('jname', 'schedname')
        assert cls._name == 'jname'
        assert cls._schedule_name == 'schedname'
        assert cls._started is False
        assert cls._finished is False
        assert cls._exit_code == -1
        assert cls._output is None
        assert cls._start_time is None
        assert cls._finish_time is None
        assert cls._summary_regex is None
        assert cls._skip is False

    def test_init_regex(self):
        cls = Job('jname', 'schedname', summary_regex='foobar')
        assert cls._name == 'jname'
        assert cls._schedule_name == 'schedname'
        assert cls._started is False
        assert cls._finished is False
        assert cls._exit_code == -1
        assert cls._output is None
        assert cls._start_time is None
        assert cls._finish_time is None
        assert cls._summary_regex == 'foobar'
        assert cls._skip is False

    def test_name(self):
        assert self.cls.name == 'jname'

    def test_skip(self):
        assert self.cls.skip is False

    def test_skip_true(self):
        self.cls._skip = True
        assert self.cls.skip is True

    def test_schedule_name(self):
        assert self.cls.schedule_name == 'schedname'

    def test_is_started(self):
        self.cls._started = 2
        assert self.cls.is_started == 2

    def test_is_finished(self):
        self.cls._finished = 7
        assert self.cls.is_finished == 7

    def test_run(self):
        with pytest.raises(NotImplementedError):
            self.cls.run()

    def test_poll(self):
        self.cls._finished = 6
        assert self.cls.poll() == 6

    def test_exit_code(self):
        self.cls._exit_code = 23
        assert self.cls.exitcode == 23

    def test_output(self):
        self.cls._output = 'foo'
        assert self.cls.output == 'foo'

    def test_repr(self):
        assert self.cls.__repr__() == '<Job name="jname">'

    def test_duration(self):
        self.cls._start_time = datetime(2017, 11, 23, 14, 52, 34)
        td = timedelta(seconds=3668)
        self.cls._finish_time = self.cls._start_time + td
        assert self.cls.duration == td

    def test_error_repr(self):
        self.cls._started = True
        self.cls._output = 'foobar'
        expected = "<Job name=\"%s\">\nSchedule Name: %s\nStarted: %s\n" \
                   "Finished: %s\nDuration: %s\nExit Code: %s\nOutput: %s\n" % (
                       'jname', 'schedname', True, False, None, -1, 'foobar'
                   )
        assert self.cls.error_repr == expected


class TestBaseJobSummary(object):

    def setup(self):
        self.cls = Job('jname', 'schedname')

    def test_summary_one_line(self):
        self.cls._output = 'foo'
        assert self.cls.summary() == 'foo'

    def test_summary(self):
        self.cls._output = "foo\n\n \nbar\n"
        assert self.cls.summary() == 'bar'

    def test_none(self):
        self.cls._output = None
        assert self.cls.summary() == ''

    def test_short(self):
        self.cls._output = "\n \n"
        assert self.cls.summary() == ''

    def test_regex_one(self):
        self.cls._summary_regex = '^f.*$'
        self.cls._output = "foo\n"
        assert self.cls.summary() == 'foo'

    def test_regex_multiple(self):
        self.cls._summary_regex = '^f.*$'
        self.cls._output = "foo\nfie\nfoe\nbar\nfit\nbaz"
        assert self.cls.summary() == 'fit'

    def test_regex_no_match(self):
        self.cls._summary_regex = '^f.*$'
        self.cls._output = "\nbar\nbaz\nblam"
        assert self.cls.summary() == 'blam'
