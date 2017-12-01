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
from unittest.mock import Mock, patch, call, DEFAULT, PropertyMock
from stat import S_IRUSR, S_IWUSR, S_IXUSR

import pytest
from freezegun import freeze_time

from ecsjobs.jobs.local_command import LocalCommand

pbm = 'ecsjobs.jobs.local_command'
pb = '%s.LocalCommand' % pbm


class TestLocalCommand(object):

    def test_init(self):
        cls = LocalCommand('jname', 'sname', command='foo')
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._shell is False
        assert cls._timeout is None
        assert cls._script_source is None
        assert cls._summary_regex is None
        assert cls._command == 'foo'
        assert cls._exit_code is None

    def test_init_all_options(self):
        cls = LocalCommand(
            'jname', 'sname', summary_regex='foo', command='/bin/bar',
            shell=True, timeout=23
        )
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._command == '/bin/bar'
        assert cls._shell is True
        assert cls._timeout == 23
        assert cls._script_source is None
        assert cls._summary_regex == 'foo'
        assert cls._exit_code is None

    def test_init_no_cmd_or_script(self):
        with pytest.raises(RuntimeError):
            LocalCommand('jname', 'sname')


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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = '/my/temp/file'
                        res = self.cls.run()
        assert res is True
        assert self.cls._exit_code == 0
        assert self.cls._output == 'hello'
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert m_unlink.mock_calls == []
        assert m_gs.mock_calls == []
        assert m_run.mock_calls == [
            call(
                ['/usr/bin/cmd', '-h'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]

    def test_success_script_command_arr(self):
        self.cls._script_source = 's3://foo/bar'
        self.cls._command = ['foo', 'bar']
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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = ['/my/temp/file', 'foo', 'bar']
                        res = self.cls.run()
        assert res is True
        assert self.cls._exit_code == 0
        assert self.cls._output == 'hello'
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert self.cls._command == ['/my/temp/file', 'foo', 'bar']
        assert m_unlink.mock_calls == [call('/my/temp/file')]
        assert m_gs.mock_calls == [call(self.cls, 's3://foo/bar')]
        assert m_run.mock_calls == [
            call(
                ['/my/temp/file', 'foo', 'bar'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]

    def test_success_script_command_str(self):
        self.cls._script_source = 's3://foo/bar'
        self.cls._command = ''
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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = '/my/temp/file'
                        res = self.cls.run()
        assert res is True
        assert self.cls._exit_code == 0
        assert self.cls._output == 'hello'
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert self.cls._command == '/my/temp/file'
        assert m_unlink.mock_calls == [call('/my/temp/file')]
        assert m_gs.mock_calls == [call(self.cls, 's3://foo/bar')]
        assert m_run.mock_calls == [
            call(
                '/my/temp/file',
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]

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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = '/my/temp/file'
                        with pytest.raises(subprocess.TimeoutExpired):
                            self.cls.run()
        assert self.cls._exit_code is None
        assert self.cls._output == "foo"
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert m_unlink.mock_calls == []
        assert m_gs.mock_calls == []
        assert m_run.mock_calls == [
            call(
                ['/usr/bin/cmd', '-h'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]

    def test_timeout_script_command_str(self):
        self.cls._script_source = 's3://foo/bar'
        self.cls._command = '/foo/bar'
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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = '/my/temp/file'
                        with pytest.raises(subprocess.TimeoutExpired):
                            self.cls.run()
        assert self.cls._exit_code is None
        assert self.cls._output == "foo"
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert self.cls._command == '/my/temp/file'
        assert m_unlink.mock_calls == [call('/my/temp/file')]
        assert m_gs.mock_calls == [call(self.cls, 's3://foo/bar')]
        assert m_run.mock_calls == [
            call(
                '/my/temp/file',
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]

    def test_timeout_script_command_arr(self):
        self.cls._script_source = 's3://foo/bar'
        self.cls._command = ['foo', 'bar']
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
                with patch('%s.unlink' % pbm) as m_unlink:
                    with patch('%s._get_script' % pb, autospec=True) as m_gs:
                        m_gs.return_value = ['/my/temp/file', 'foo', 'bar']
                        with pytest.raises(subprocess.TimeoutExpired):
                            self.cls.run()
        assert self.cls._exit_code is None
        assert self.cls._output == "foo"
        assert self.cls._finished is True
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._finish_time == self.second_dt
        assert self.cls._command == ['/my/temp/file', 'foo', 'bar']
        assert m_unlink.mock_calls == [call('/my/temp/file')]
        assert m_gs.mock_calls == [call(self.cls, 's3://foo/bar')]
        assert m_run.mock_calls == [
            call(
                ['/my/temp/file', 'foo', 'bar'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                timeout=None
            )
        ]


class TestLocalCommandReportDescription(object):

    def setup(self):
        self.cls = LocalCommand(
            'jname',
            'sname',
            command=['/usr/bin/cmd', '-h']
        )

    def test_report_description(self):
        assert self.cls.report_description() == ['/usr/bin/cmd', '-h']

    def test_report_description_script_source(self):
        self.cls._script_source = 'http://foo'
        assert self.cls.report_description() == 'http://foo'


class TestLocalCommandGetScript(object):

    def setup(self):
        self.cls = LocalCommand(
            'jname',
            'sname',
            command=['/usr/bin/cmd', '-h']
        )

    def test_boto(self):
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        self.cls._command = ''

        m_client = Mock()
        m_body = Mock()
        m_body.read.return_value = b'myContent'
        m_client.get_object.return_value = {
            'Body': m_body
        }
        m_fd = Mock()

        with patch.multiple(
            pbm,
            **{
                'boto3': DEFAULT,
                'requests': DEFAULT,
                'mkstemp': DEFAULT,
                'chmod': DEFAULT,
                'fdopen': DEFAULT
            }
        ) as mocks:
            mocks['boto3'].client.return_value = m_client
            mocks['mkstemp'].return_value = m_fd, '/tmp/tmpfile'
            res = self.cls._get_script('s3://bktname/path/to/key')
        assert res == '/tmp/tmpfile'
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        assert mocks['boto3'].mock_calls == [
            call.client('s3'),
            call.client().get_object(Bucket='bktname', Key='path/to/key')
        ]
        assert m_client.mock_calls == [
            call.get_object(Bucket='bktname', Key='path/to/key')
        ]
        assert mocks['requests'].mock_calls == []
        assert mocks['mkstemp'].mock_calls == [
            call('ecsjobs-jname')
        ]
        assert mocks['chmod'].mock_calls == [
            call('/tmp/tmpfile', S_IRUSR | S_IWUSR | S_IXUSR)
        ]
        assert mocks['fdopen'].mock_calls == [
            call(m_fd, 'wb'),
            call().write(b'myContent'),
            call().close()
        ]

    def test_boto_with_args(self):
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        self.cls._command = ['foo', 'bar', 'baz']

        m_client = Mock()
        m_body = Mock()
        m_body.read.return_value = 'myContent'
        m_client.get_object.return_value = {
            'Body': m_body
        }
        m_fd = Mock()

        with patch.multiple(
            pbm,
            **{
                'boto3': DEFAULT,
                'requests': DEFAULT,
                'mkstemp': DEFAULT,
                'chmod': DEFAULT,
                'fdopen': DEFAULT
            }
        ) as mocks:
            mocks['boto3'].client.return_value = m_client
            mocks['mkstemp'].return_value = m_fd, '/tmp/tmpfile'
            res = self.cls._get_script('s3://bktname/path/to/key')
        assert res == ['/tmp/tmpfile', 'foo', 'bar', 'baz']
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        assert mocks['boto3'].mock_calls == [
            call.client('s3'),
            call.client().get_object(Bucket='bktname', Key='path/to/key')
        ]
        assert m_client.mock_calls == [
            call.get_object(Bucket='bktname', Key='path/to/key')
        ]
        assert mocks['requests'].mock_calls == []
        assert mocks['mkstemp'].mock_calls == [
            call('ecsjobs-jname')
        ]
        assert mocks['chmod'].mock_calls == [
            call('/tmp/tmpfile', S_IRUSR | S_IWUSR | S_IXUSR)
        ]
        assert mocks['fdopen'].mock_calls == [
            call(m_fd, 'w'),
            call().write('myContent'),
            call().close()
        ]

    def test_http(self):
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        self.cls._command = []

        m_resp = Mock()
        type(m_resp).text = PropertyMock(return_value='foobar')
        m_fd = Mock()

        with patch.multiple(
            pbm,
            **{
                'boto3': DEFAULT,
                'requests': DEFAULT,
                'mkstemp': DEFAULT,
                'chmod': DEFAULT,
                'fdopen': DEFAULT
            }
        ) as mocks:
            mocks['requests'].get.return_value = m_resp
            mocks['mkstemp'].return_value = m_fd, '/tmp/tmpfile'
            res = self.cls._get_script('http://bar')
        assert res == '/tmp/tmpfile'
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        assert mocks['boto3'].mock_calls == []
        assert mocks['requests'].mock_calls == [
            call.get('http://bar')
        ]
        assert mocks['mkstemp'].mock_calls == [
            call('ecsjobs-jname')
        ]
        assert mocks['chmod'].mock_calls == [
            call('/tmp/tmpfile', S_IRUSR | S_IWUSR | S_IXUSR)
        ]
        assert mocks['fdopen'].mock_calls == [
            call(m_fd, 'w'),
            call().write('foobar'),
            call().close()
        ]

    def test_http_with_args(self):
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        self.cls._command = 'foobar'

        m_resp = Mock()
        type(m_resp).text = PropertyMock(return_value='foobar')
        m_fd = Mock()

        with patch.multiple(
            pbm,
            **{
                'boto3': DEFAULT,
                'requests': DEFAULT,
                'mkstemp': DEFAULT,
                'chmod': DEFAULT,
                'fdopen': DEFAULT
            }
        ) as mocks:
            mocks['requests'].get.return_value = m_resp
            mocks['mkstemp'].return_value = m_fd, '/tmp/tmpfile'
            res = self.cls._get_script('http://bar')
        assert res == ['/tmp/tmpfile', 'foobar']
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        assert mocks['boto3'].mock_calls == []
        assert mocks['requests'].mock_calls == [
            call.get('http://bar')
        ]
        assert mocks['mkstemp'].mock_calls == [
            call('ecsjobs-jname')
        ]
        assert mocks['chmod'].mock_calls == [
            call('/tmp/tmpfile', S_IRUSR | S_IWUSR | S_IXUSR)
        ]
        assert mocks['fdopen'].mock_calls == [
            call(m_fd, 'w'),
            call().write('foobar'),
            call().close()
        ]

    def test_unsupported_url(self):
        assert self.cls.is_started is False
        assert self.cls.is_finished is False
        assert self.cls.exitcode is None
        assert self.cls.output is None
        with patch.multiple(
            pbm,
            **{
                'boto3': DEFAULT,
                'requests': DEFAULT,
                'mkstemp': DEFAULT,
                'chmod': DEFAULT,
                'fdopen': DEFAULT
            }
        ) as mocks:
            with pytest.raises(RuntimeError) as exc:
                self.cls._get_script('foo://bar')
        assert str(exc.value) == 'Error: unsupported URL scheme: foo://bar'
        assert mocks['boto3'].mock_calls == []
        assert mocks['requests'].mock_calls == []
        assert mocks['mkstemp'].mock_calls == []
        assert mocks['chmod'].mock_calls == []
        assert mocks['fdopen'].mock_calls == []
