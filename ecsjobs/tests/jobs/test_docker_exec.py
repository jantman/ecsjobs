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

from unittest.mock import patch, call, Mock, PropertyMock
from freezegun import freeze_time
from ecsjobs.jobs.docker_exec import DockerExec

pbm = 'ecsjobs.jobs.docker_exec'
pb = '%s.DockerExec' % pbm


class TestDockerExecInit(object):

    def test_init(self):
        cls = DockerExec('jname', 'sname', container_name='cname',
                         command='/my/cmd')
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._summary_regex is None
        assert cls._cron_expression is None
        assert cls._container_name == 'cname'
        assert cls._command == '/my/cmd'
        assert cls._tty is False
        assert cls._stdout is True
        assert cls._stderr is True
        assert cls._privileged is False
        assert cls._user == 'root'
        assert cls._environment is None
        assert cls._docker is None
        assert cls._container is None

    @freeze_time('2017-11-23 12:32:53')
    def test_init_all_options(self):
        mock_cronex = Mock()
        with patch('ecsjobs.jobs.base.CronExpression') as m_cronex:
            m_cronex.return_value = mock_cronex
            cls = DockerExec(
                'jname',
                'sname',
                summary_regex='foo',
                cron_expression='crex',
                container_name='cname',
                command='/my/command',
                tty=True,
                stdout=False,
                stderr=False,
                privileged=True,
                user='uname',
                environment={'ENV': 'var'}
            )
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._summary_regex == 'foo'
        assert cls._cron_expression == mock_cronex
        assert cls._container_name == 'cname'
        assert cls._command == '/my/command'
        assert cls._tty is True
        assert cls._stdout is False
        assert cls._stderr is False
        assert cls._privileged is True
        assert cls._user == 'uname'
        assert cls._environment == {'ENV': 'var'}
        assert cls._docker is None
        assert cls._container is None
        assert m_cronex.mock_calls == [
            call('crex'),
            call().check_trigger((2017, 11, 23, 12, 32))
        ]


class TestDockerExec(object):

    def setup(self):
        self.cls = DockerExec(
            'jname', 'sname',
            container_name='contname',
            command='/my/command'
        )

    def test_exit_zero(self):
        with patch('%s._docker_run' % pb, autospec=True) as mock_docker_run:
            self.cls._exit_code = 0
            res = self.cls.run()
        assert res is True
        assert mock_docker_run.mock_calls == [call(self.cls)]

    def test_exit_non_zero(self):
        with patch('%s._docker_run' % pb, autospec=True) as mock_docker_run:
            self.cls._exit_code = 24
            res = self.cls.run()
        assert res is False
        assert mock_docker_run.mock_calls == [call(self.cls)]

    def test_report_description(self):
        assert self.cls.report_description() == 'contname: /my/command'

    def test_error_repr(self):
        self.cls._exit_code = 6
        self.cls._container = Mock()
        type(self.cls._container).short_id = PropertyMock(return_value='abcd12')
        with patch(
            '%s.duration' % pb, new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = 'dstr'
            res = self.cls.error_repr
        expected = "%s\nSchedule Name: sname\nStarted: False\n" \
                   "Finished: False\nDuration: dstr\nExit Code: 6\n" \
                   "Container Name: contname\nContainer ID: abcd12\n" \
                   "TTY: False\nPrivileged: False\nEnvironment: None\n" \
                   "Output: None\n" % self.cls.__repr__()
        assert res == expected

    def test_error_repr_exitcode_none(self):
        self.cls._exit_code = None
        self.cls._container = Mock()
        type(self.cls._container).short_id = PropertyMock(return_value='abcd12')
        with patch(
            '%s.duration' % pb, new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = 'dstr'
            res = self.cls.error_repr
        expected = "%s\nSchedule Name: sname\nStarted: False\n" \
                   "Finished: False\nDuration: dstr\n" \
                   "Container Name: contname\nContainer ID: abcd12\n" \
                   "TTY: False\nPrivileged: False\nEnvironment: None\n" \
                   "Output: None\n" % self.cls.__repr__()
        assert res == expected

    def test_error_repr_no_container_id(self):
        self.cls._exit_code = 6
        self.cls._container = Mock()
        del self.cls._container.short_id
        with patch(
            '%s.duration' % pb, new_callable=PropertyMock
        ) as mock_duration:
            mock_duration.return_value = 'dstr'
            res = self.cls.error_repr
        expected = "%s\nSchedule Name: sname\nStarted: False\n" \
                   "Finished: False\nDuration: dstr\nExit Code: 6\n" \
                   "Container Name: contname\n" \
                   "TTY: False\nPrivileged: False\nEnvironment: None\n" \
                   "Output: None\n" % self.cls.__repr__()
        assert res == expected
