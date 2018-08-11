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

from unittest.mock import patch, Mock, call, DEFAULT, PropertyMock, mock_open
from datetime import datetime, timedelta
from subprocess import PIPE, STDOUT

import pytest
from freezegun import freeze_time

from ecsjobs.reporter import Reporter
from ecsjobs.jobs.base import Job

pbm = 'ecsjobs.reporter'
pb = '%s.Reporter' % pbm


class ReportTester(object):

    def setup(self):
        self.client = Mock()
        self.mock_conf = Mock()
        self.from_email = 'from@example.com'
        self.to_email = ['to1@foo.com', 'to2@foo.com']
        self.failure_html_path = None
        self.failure_command = None

        def se_conf_get(k):
            if k == 'from_email':
                return self.from_email
            elif k == 'to_email':
                return self.to_email
            elif k == 'email_subject':
                return 'MySubject'
            elif k == 'failure_html_path':
                return self.failure_html_path
            elif k == 'failure_command':
                return self.failure_command
            return None

        self.mock_conf.get_global.side_effect = se_conf_get
        with patch('%s.boto3.client' % pbm) as m_boto:
            m_boto.return_value = self.client
            self.cls = Reporter(self.mock_conf)


class TestInit(object):

    def test_init(self):
        conf = Mock()
        with patch('%s.boto3.client' % pbm) as m_boto:
            cls = Reporter(conf)
        assert cls._config == conf
        assert m_boto.mock_calls == [call('ses')]
        assert cls._ses == m_boto.return_value


class TestRun(ReportTester):

    def test_run(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    self.cls.run(
                        m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt
                    )
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com', 'to2@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == []
        assert mocks['mkstemp'].mock_calls == []
        assert mocks['Popen'].mock_calls == []
        assert mocks['os_close'].mock_calls == []

    def test_run_only_if_problems(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    self.cls.run(
                        m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt,
                        only_email_if_problems=True
                    )
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == []
        assert m_open.mock_calls == []
        assert mocks['mkstemp'].mock_calls == []
        assert mocks['Popen'].mock_calls == []
        assert mocks['os_close'].mock_calls == []

    def test_run_to_str(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()
        self.to_email = 'to1@foo.com'

        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    self.cls.run(
                        m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt
                    )
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == []
        assert mocks['mkstemp'].mock_calls == []
        assert mocks['Popen'].mock_calls == []
        assert mocks['os_close'].mock_calls == []

    def test_run_exception_default(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        self.client.send_email.side_effect = RuntimeError('foo')
        self.failure_html_path = None
        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    with pytest.raises(RuntimeError) as exc:
                        self.cls.run(
                            m_finished, m_unfinished, m_excs, m_start_dt,
                            m_end_dt
                        )
        assert str(exc.value) == 'foo'
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com', 'to2@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == [
            call('/tmp/path', 'w'),
            call().__enter__(),
            call().write('my_html_report'),
            call().__exit__(None, None, None)
        ]
        assert mocks['mkstemp'].mock_calls == [
            call(prefix='ecsjobs', text=True, suffix='.html')
        ]
        assert mocks['Popen'].mock_calls == []
        assert mocks['os_close'].mock_calls == [call(999)]

    def test_run_exception_failure_cmd(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        self.client.send_email.side_effect = RuntimeError('foo')
        self.failure_command = ['/bin/something', 'foo']
        m_open = mock_open()
        m_popen = Mock()
        m_popen.communicate.return_value = ('my_output', None)
        type(m_popen).returncode = 0
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    mocks['Popen'].return_value = m_popen
                    with pytest.raises(RuntimeError) as exc:
                        self.cls.run(
                            m_finished, m_unfinished, m_excs, m_start_dt,
                            m_end_dt
                        )
        assert str(exc.value) == 'foo'
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com', 'to2@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == [
            call('/tmp/path', 'w'),
            call().__enter__(),
            call().write('my_html_report'),
            call().__exit__(None, None, None)
        ]
        assert mocks['mkstemp'].mock_calls == [
            call(prefix='ecsjobs', text=True, suffix='.html')
        ]
        assert mocks['Popen'].mock_calls == [
            call(
                '/bin/something', 'foo', stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                universal_newlines=True
            ),
            call().communicate(input='\n\nmy_html_report', timeout=120)
        ]
        assert mocks['os_close'].mock_calls == [call(999)]

    def test_run_exception_failure_cmd_failure(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        self.client.send_email.side_effect = RuntimeError('foo')
        self.failure_command = ['/bin/something', 'foo']
        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    mocks['Popen'].return_value = RuntimeError()
                    with pytest.raises(RuntimeError) as exc:
                        self.cls.run(
                            m_finished, m_unfinished, m_excs, m_start_dt,
                            m_end_dt
                        )
        assert str(exc.value) == 'foo'
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com', 'to2@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == [
            call('/tmp/path', 'w'),
            call().__enter__(),
            call().write('my_html_report'),
            call().__exit__(None, None, None)
        ]
        assert mocks['mkstemp'].mock_calls == [
            call(prefix='ecsjobs', text=True, suffix='.html')
        ]
        assert mocks['Popen'].mock_calls == [
            call(
                '/bin/something', 'foo', stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                universal_newlines=True
            )
        ]
        assert mocks['os_close'].mock_calls == [call(999)]

    def test_run_failure_path(self):
        m_finished = Mock()
        m_unfinished = Mock()
        m_excs = Mock()
        m_start_dt = Mock()
        m_end_dt = Mock()

        self.client.send_email.side_effect = RuntimeError('foo')
        self.failure_html_path = '/fail/path'
        m_open = mock_open()
        with patch('%s._make_report' % pb) as mock_mr:
            with patch('%s.open' % pbm, m_open, create=True):
                with patch.multiple(
                    pbm,
                    mkstemp=DEFAULT,
                    Popen=DEFAULT,
                    os_close=DEFAULT
                ) as mocks:
                    mocks['mkstemp'].return_value = (999, '/tmp/path')
                    mock_mr.return_value = 'my_html_report'
                    with pytest.raises(RuntimeError) as exc:
                        self.cls.run(
                            m_finished, m_unfinished, m_excs, m_start_dt,
                            m_end_dt
                        )
        assert str(exc.value) == 'foo'
        assert mock_mr.mock_calls == [
            call(m_finished, m_unfinished, m_excs, m_start_dt, m_end_dt)
        ]
        assert self.client.mock_calls == [
            call.send_email(
                Source='from@example.com',
                Destination={
                    'ToAddresses': ['to1@foo.com', 'to2@foo.com']
                },
                Message={
                    'Subject': {
                        'Data': 'MySubject',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': 'my_html_report',
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath='from@example.com'
            )
        ]
        assert m_open.mock_calls == [
            call('/fail/path', 'w'),
            call().__enter__(),
            call().write('my_html_report'),
            call().__exit__(None, None, None)
        ]
        assert mocks['mkstemp'].mock_calls == []
        assert mocks['os_close'].mock_calls == []
        assert mocks['Popen'].mock_calls == []


class TestMakeReport(ReportTester):

    @freeze_time('2017-11-23 12:34:56')
    def test_make_report(self):
        j1 = Mock(spec_set=Job, name='job1')
        type(j1).name = PropertyMock(return_value='job1')
        j2 = Mock(spec_set=Job, name='job2')
        type(j2).name = PropertyMock(return_value='job2')
        j3 = Mock(spec_set=Job, name='job3')
        type(j3).name = PropertyMock(return_value='job3')
        m_exc = Mock()
        excs = {j2: m_exc}
        finished = [j1, j2]
        unfinished = [j3]
        s_dt = datetime(2017, 11, 12, 13, 00, 00)
        e_dt = datetime(2017, 11, 12, 14, 2, 33)
        expected = "<p>ECSJobs run report for uname@hname at " \
                   "Thursday, 2017-11-23 12:34:56 </p>\n" \
                   "<p>Total Duration: 1:02:33</p>\n" \
                   "<table style=\"border: 1px solid black; border-collapse: " \
                   "collapse;\">\n<tr>" \
                   "<th style=\"border: 1px solid black;\">Job Name</th>" \
                   "<th style=\"border: 1px solid black;\">Exit Code</th>" \
                   "<th style=\"border: 1px solid black;\">Duration</th>" \
                   "<th style=\"border: 1px solid black;\">Message</th>" \
                   "</tr>\n" \
                   "tr-job1\ntr-job2\ntr-job3\n" \
                   "</table>\n" \
                   "div-job1\n<hr />\n" \
                   "div-job2\n<hr />\n" \
                   "div-job3\n<hr />\n"

        def se_tr(cls, j, exc=None, unfinished=False):
            return "tr-%s\n" % j.name

        def se_div(cls, j, exc=None, unfinished=False):
            return "div-%s\n" % j.name

        with patch.multiple(
            pb,
            autospec=True,
            _tr_for_job=DEFAULT,
            _div_for_job=DEFAULT
        ) as mocks:
            mocks['_tr_for_job'].side_effect = se_tr
            mocks['_div_for_job'].side_effect = se_div
            with patch.multiple(
                pbm,
                autospec=True,
                getuser=DEFAULT,
                gethostname=DEFAULT
            ) as modmocks:
                modmocks['getuser'].return_value = 'uname'
                modmocks['gethostname'].return_value = 'hname'
                res = self.cls._make_report(
                    finished, unfinished, excs, s_dt, e_dt
                )
        assert res == expected
        assert self.cls._have_failures is False
        assert mocks['_tr_for_job'].mock_calls == [
            call(self.cls, j1, exc=None),
            call(self.cls, j2, exc=m_exc),
            call(self.cls, j3, unfinished=True)
        ]
        assert mocks['_div_for_job'].mock_calls == [
            call(self.cls, j1, exc=None),
            call(self.cls, j2, exc=m_exc),
            call(self.cls, j3, unfinished=True)
        ]
        assert modmocks['getuser'].mock_calls == [call()]
        assert modmocks['gethostname'].mock_calls == [call()]


class TestTd(ReportTester):

    def test_td(self):
        expected = '<td style="border: 1px solid black; padding: 1em;">%s' \
                   '</td>' % 'foo'
        assert self.cls.td('foo') == expected


class TestTrForJob(ReportTester):

    def test_simple(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #66ff66;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>0</td>' \
                   '<td>0:01:05</td>' \
                   '<td>summary</td>' \
                   '</tr>' + "\n"

        def se_td(_, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j)
        assert res == expected
        assert self.cls._have_failures is False

    def test_skip(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=None)
        type(j).duration = PropertyMock(return_value=None)
        type(j).is_finished = PropertyMock(return_value=None)
        type(j).skip = PropertyMock(return_value='skip reason')
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #fffc4d;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>Skipped</td>' \
                   '<td>&nbsp;</td>' \
                   '<td>skip reason</td>' \
                   '</tr>' + "\n"

        def se_td(_, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j)
        assert res == expected
        assert self.cls._have_failures is False

    def test_non_zero(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=23)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #ff9999;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>23</td>' \
                   '<td>0:01:05</td>' \
                   '<td>summary</td>' \
                   '</tr>' + "\n"

        def se_td(_, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j)
        assert res == expected
        assert self.cls._have_failures is True

    def test_less_than_zero(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=-2)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #ff9999;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>-2</td>' \
                   '<td>0:01:05</td>' \
                   '<td>summary</td>' \
                   '</tr>' + "\n"

        def se_td(_, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j)
        assert res == expected
        assert self.cls._have_failures is True

    def test_unfinished(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #ff944d;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>Unfinished</td>' \
                   '<td>0:01:05</td>' \
                   '<td><em>Unfinished</em></td>' \
                   '</tr>' + "\n"

        def se_td(cls, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j, unfinished=True)
        assert res == expected
        assert self.cls._have_failures is True

    def test_exception(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).error_repr = PropertyMock(return_value='erpr')
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        expected = '<tr style="background-color: #ff9999;">' \
                   '<td><a href="#myjob">myjob</a></td>' \
                   '<td>Exception</td>' \
                   '<td>0:01:05</td>' \
                   '<td>RuntimeError: foo</td>' \
                   '</tr>' + "\n"

        def se_td(cls, s):
            return '<td>%s</td>' % s

        with patch('%s.td' % pb, autospec=True) as mock_td:
            mock_td.side_effect = se_td
            res = self.cls._tr_for_job(j, exc=(RuntimeError('foo'), 'tb'))
        assert res == expected
        assert self.cls._have_failures is True


class TestDivForJob(ReportTester):

    def test_simple(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).error_repr = PropertyMock(return_value='erpr')
        type(j).output = PropertyMock(return_value='jobOutput')
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        j.report_description.return_value = 'Job Description'
        expected = '<div><p><strong><a name="myjob">myjob</a></strong> - ' \
                   'Job Description</p><pre>jobOutput</pre></div>' + "\n"
        assert self.cls._div_for_job(j) == expected

    def test_skip(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=None)
        type(j).duration = PropertyMock(return_value=None)
        type(j).is_finished = PropertyMock(return_value=False)
        type(j).error_repr = PropertyMock(return_value='erpr')
        type(j).output = PropertyMock(return_value='jobOutput')
        type(j).skip = PropertyMock(return_value='skip reason')
        j.summary.return_value = 'summary'
        j.report_description.return_value = 'Job Description'
        expected = '<div><p><strong><a name="myjob">myjob</a></strong> - ' \
                   'Job Description</p><p>Job Skipped: skip reason</p>' \
                   '</div>' + "\n"
        assert self.cls._div_for_job(j) == expected

    def test_unfinished(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).error_repr = PropertyMock(return_value='erpr')
        type(j).output = PropertyMock(return_value='jobOutput')
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        j.report_description.return_value = 'Job Description'
        expected = '<div><p><strong><a name="myjob">myjob</a></strong> - ' \
                   'Job Description</p><pre>erpr</pre>\n<strong>JOB ' \
                   'NOT FINISHED.</strong></div>' + "\n"
        assert self.cls._div_for_job(j, unfinished=True) == expected

    def test_exc(self):
        j = Mock(spec_set=Job)
        type(j).name = PropertyMock(return_value='myjob')
        type(j).exitcode = PropertyMock(return_value=0)
        type(j).duration = PropertyMock(return_value=timedelta(seconds=65))
        type(j).is_finished = PropertyMock(return_value=True)
        type(j).error_repr = PropertyMock(return_value='erpr')
        type(j).output = PropertyMock(return_value='jobOutput')
        type(j).skip = PropertyMock(return_value=None)
        j.summary.return_value = 'summary'
        j.report_description.return_value = 'Job Description'
        expected = '<div><p><strong><a name="myjob">myjob</a></strong> - ' \
                   'Job Description</p><pre>erpr\n\ntb</pre>' \
                   '</div>' + "\n"
        assert self.cls._div_for_job(
            j, exc=(RuntimeError('foo'), 'tb')) == expected
