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

import subprocess
from datetime import datetime
from unittest.mock import Mock, patch

from freezegun import freeze_time

from ecsjobs.jobs.local_command import LocalCommand

pbm = 'ecsjobs.jobs.local_command'


class TestLocalCommand(object):

    def test_init(self):
        cls = LocalCommand('jname', 'sname', foo='bar')
        assert cls._config == {
            'foo': 'bar',
            'shell': False,
            'timeout': None
        }


class TestLocalCommandRun(object):

    def setup(self):
        self.cls = LocalCommand(
            'jname',
            'sname',
            command=['/usr/bin/cmd', '-h']
        )

    def test_success(self):
        self.frozen = None
        self.second_dt = datetime(2017, 10, 20, 12, 35, 00)
        self.retval = Mock(
            spec=subprocess.CompletedProcess,
            returncode=0, stdout=b'hello'
        )

        def se_run(*args, **kwargs):
            self.frozen.move_to(self.second_dt)
            return self.retval

        initial_dt = datetime(2017, 10, 20, 12, 30, 00)
        with freeze_time(initial_dt) as frozen:
            self.frozen = frozen
            with patch('%s.subprocess.run' % pbm) as m_run:
                m_run.side_effect = se_run
                res = self.cls.run()
        assert res is True
        assert self.cls._exit_code == 0
        assert self.cls._output == 'hello'
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt

    def test_timeout(self):
        self.frozen = None
        self.second_dt = datetime(2017, 10, 20, 12, 35, 00)

        def se_run(*args, **kwargs):
            self.frozen.move_to(self.second_dt)
            raise subprocess.TimeoutExpired(
                ['/usr/bin/cmd', '-h'], 120, output=b'foo'
            )

        initial_dt = datetime(2017, 10, 20, 12, 30, 00)
        with freeze_time(initial_dt) as frozen:
            self.frozen = frozen
            with patch('%s.subprocess.run' % pbm) as m_run:
                m_run.side_effect = se_run
                res = self.cls.run()
        assert res is False
        assert self.cls._exit_code == -2
        assert self.cls._output == 'foo'
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt


class TestLocalCommandSummary(object):

    def setup(self):
        self.cls = LocalCommand(
            'jname',
            'sname',
            command=['/usr/bin/cmd', '-h']
        )

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
