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

import logging
import pytest
from datetime import datetime
from unittest.mock import patch, call, Mock, DEFAULT, PropertyMock

from freezegun import freeze_time

from ecsjobs.runner import (
    set_log_debug, set_log_info, set_log_level_format, parse_args, main,
    EcsJobsRunner
)
from ecsjobs.version import VERSION, PROJECT_URL

pbm = 'ecsjobs.runner'
pb = '%s.EcsJobsRunner' % pbm


class MockArgs(object):

    def __init__(self, **kwargs):
        self.verbose = 0
        self.ACTION = None
        self.SCHEDULES = []
        self.only_email_if_problems = False
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestParseArgs(object):

    def test_parse_args_list_schedules(self):
        res = parse_args(['-v', 'list-schedules'])
        assert res.verbose == 1
        assert res.ACTION == 'list-schedules'
        assert res.SCHEDULES == []
        assert res.only_email_if_problems is False

    def test_parse_args_validate(self):
        res = parse_args(['-vv', 'validate'])
        assert res.verbose == 2
        assert res.ACTION == 'validate'
        assert res.SCHEDULES == []
        assert res.only_email_if_problems is False

    def test_parse_args_run_none(self):
        with pytest.raises(RuntimeError) as exc:
            parse_args(['run'])
        assert str(exc.value) == 'ERROR: "run" action must have one or ' \
                                 'more SCHEDULES specified if jobs are not ' \
                                 'explicitly specified with -j / --job'

    def test_parse_args_run_one(self):
        res = parse_args(['run', 'foo'])
        assert res.verbose == 0
        assert res.ACTION == 'run'
        assert res.SCHEDULES == ['foo']
        assert res.only_email_if_problems is False

    def test_parse_args_run_three(self):
        res = parse_args(['-m', '-v', 'run', 'foo', 'bar', 'baz'])
        assert res.verbose == 1
        assert res.ACTION == 'run'
        assert res.SCHEDULES == ['foo', 'bar', 'baz']
        assert res.only_email_if_problems is True

    def test_parse_args_version(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args(['-V'])
        assert excinfo.value.code == 0
        expected = "ecsjobs v%s <%s>\n" % (
            VERSION, PROJECT_URL
        )
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''

    def test_parse_args_jobs(self):
        res = parse_args(
            ['--only-email-if-problems', '-v', 'run', '-j', 'bar', '--job=baz']
        )
        assert res.verbose == 1
        assert res.ACTION == 'run'
        assert res.SCHEDULES == []
        assert res.jobs == ['bar', 'baz']
        assert res.only_email_if_problems is True

    def test_parse_args_jobs_and_schedules(self):
        with pytest.raises(RuntimeError) as exc:
            parse_args(['-v', '-j', 'bar', '--job=baz', 'run', 'foo'])
        assert str(exc.value) == 'ERROR: SCHEDULES cannot be mixed with ' \
                                 '-j / --job.'


class TestLogSetup(object):

    def test_set_log_info(self):
        m_log = Mock()
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_info(m_log)
        assert mock_set.mock_calls == [
            call(
                m_log, logging.INFO,
                '%(asctime)s %(levelname)s:%(name)s:%(message)s'
            )
        ]

    def test_set_log_debug(self):
        m_log = Mock()
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_debug(m_log)
        assert mock_set.mock_calls == [
            call(m_log, logging.DEBUG,
                 "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                 "%(name)s.%(funcName)s() ] %(message)s")
        ]

    def test_set_log_level_format(self):
        m_log = Mock()
        mock_handler = Mock(spec_set=logging.Handler)
        with patch('%s.logging.Formatter' % pbm) as mock_formatter:
            type(m_log).handlers = [mock_handler]
            set_log_level_format(m_log, 5, 'foo')
        assert mock_formatter.mock_calls == [
            call(fmt='foo')
        ]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert m_log.mock_calls == [
            call.setLevel(5)
        ]


class TestMain(object):

    def test_version(self):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            Config=DEFAULT,
            EcsJobsRunner=DEFAULT
        ) as mocks:
            mocks['parse_args'].side_effect = SystemExit(0)
            with patch('%s.sys.argv' % pbm, ['foo', '-V']):
                with pytest.raises(SystemExit):
                    main()
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['-V'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == []
        assert mocks['EcsJobsRunner'].mock_calls == []

    def test_validate(self):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            Config=DEFAULT,
            EcsJobsRunner=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = MockArgs(
                ACTION='validate', verbose=2
            )
            with pytest.raises(SystemExit) as exc:
                main(['validate'])
        assert exc.value.code == 0
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['validate'])]
        assert mocks['set_log_debug'].mock_calls == [call(logging.getLogger())]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == [call()]
        assert mocks['EcsJobsRunner'].mock_calls == []

    def test_list_schedules(self, capsys):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            Config=DEFAULT,
            EcsJobsRunner=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = MockArgs(ACTION='list-schedules')
            type(mocks['Config'].return_value).schedule_names = \
                PropertyMock(return_value=['foo', 'bar', 'baz'])
            with pytest.raises(SystemExit) as exc:
                main(['list-schedules'])
        assert exc.value.code == 0
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['list-schedules'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == [call()]
        assert mocks['EcsJobsRunner'].mock_calls == []
        out, err = capsys.readouterr()
        assert err == ''
        assert out == "foo\nbar\nbaz\n"

    def test_run_schedules(self, capsys):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            Config=DEFAULT,
            EcsJobsRunner=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = MockArgs(
                ACTION='run', SCHEDULES=['foo', 'baz'], verbose=1, jobs=[]
            )
            main(['run', 'foo', 'baz'])
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['run', 'foo', 'baz'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == [call(logging.getLogger())]
        assert mocks['Config'].mock_calls == [call()]
        assert mocks['EcsJobsRunner'].mock_calls == [
            call(mocks['Config'].return_value, only_email_if_problems=False),
            call().run_schedules(['foo', 'baz'])
        ]

    def test_run_jobs(self, capsys):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            Config=DEFAULT,
            EcsJobsRunner=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = MockArgs(
                ACTION='run', SCHEDULES=[], verbose=1, jobs=['joba', 'jobb'],
                only_email_if_problems=True
            )
            main(['run', '-j', 'joba', '--job=jobb'])
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [
            call(['run', '-j', 'joba', '--job=jobb'])
        ]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == [call(logging.getLogger())]
        assert mocks['Config'].mock_calls == [call()]
        assert mocks['EcsJobsRunner'].mock_calls == [
            call(mocks['Config'].return_value, only_email_if_problems=True),
            call().run_job_names(['joba', 'jobb'])
        ]


class TestEcsJobsRunner(object):

    def setup(self):
        self.config = Mock()
        self.cls = EcsJobsRunner(self.config)

    def test_init(self):
        cls = EcsJobsRunner(self.config)
        assert cls._conf == self.config
        assert cls._finished == []
        assert cls._running == []
        assert cls._run_exceptions == {}
        assert cls._start_time is None
        assert cls._timeout is None
        assert cls._only_email_if_problems is False

    def test_init_only_if_problems(self):
        cls = EcsJobsRunner(self.config, only_email_if_problems=True)
        assert cls._conf == self.config
        assert cls._finished == []
        assert cls._running == []
        assert cls._run_exceptions == {}
        assert cls._start_time is None
        assert cls._timeout is None
        assert cls._only_email_if_problems is True

    def test_run_schedules(self):
        j1 = Mock(name='job1')
        j1.run.return_value = True
        j2 = Mock(name='job2')
        j2.run.return_value = None
        j3 = Mock(name='job3')
        j3.run.return_value = False
        j4 = Mock(name='job4')
        type(j4).error_repr = PropertyMock(return_value='j4erepr')
        exc = RuntimeError('foo')
        j4.run.side_effect = exc
        self.config.jobs_for_schedules.return_value = [j1, j2, j3, j4]
        with patch('%s._run_jobs' % pb, autospec=True) as mock_run:
            self.cls.run_schedules(['foo', 'bar'])
        assert mock_run.mock_calls == [call(self.cls, [j1, j2, j3, j4])]

    def test_run_job_names(self):
        j1 = Mock(name='job1')
        type(j1).name = PropertyMock(return_value='job1')
        j1.run.return_value = True
        j2 = Mock(name='job2')
        j2.run.return_value = None
        type(j2).name = PropertyMock(return_value='job2')
        j3 = Mock(name='job3')
        j3.run.return_value = False
        type(j3).name = PropertyMock(return_value='job3')
        j4 = Mock(name='job4')
        type(j4).error_repr = PropertyMock(return_value='j4erepr')
        exc = RuntimeError('foo')
        j4.run.side_effect = exc
        type(j4).name = PropertyMock(return_value='job4')
        type(self.config).jobs = PropertyMock(return_value=[j1, j2, j3, j4])
        with patch('%s._run_jobs' % pb, autospec=True) as mock_run:
            self.cls.run_job_names(['job2', 'job3'])
        assert mock_run.mock_calls == [call(self.cls, [j2, j3], force_run=True)]

    @freeze_time('2017-10-20 12:30:00')
    def test_run_jobs(self):
        j1 = Mock(name='job1')
        j1.run.return_value = True
        type(j1).skip = PropertyMock(return_value=None)
        j2 = Mock(name='job2')
        j2.run.return_value = None
        type(j2).skip = PropertyMock(return_value=None)
        j3 = Mock(name='job3')
        j3.run.return_value = False
        type(j3).skip = PropertyMock(return_value=None)
        j4 = Mock(name='job4')
        type(j4).error_repr = PropertyMock(return_value='j4erepr')
        exc = RuntimeError('foo')
        j4.run.side_effect = exc
        type(j4).skip = PropertyMock(return_value=None)
        j5 = Mock(name='job5')
        type(j5).skip = PropertyMock(return_value='some reason')
        self.config.get_global.return_value = 3600
        self.cls._finished = ['a']
        self.cls._running = ['b']
        self.cls._run_exceptions['foo'] = 6
        with patch('%s._poll_jobs' % pb, autospec=True) as mock_poll:
            with patch('%s._report' % pb, autospec=True) as mock_report:
                with patch('%s.format_exc' % pbm) as m_fmt_exc:
                    m_fmt_exc.return_value = 'm_traceback'
                    self.cls._run_jobs([j1, j2, j3, j4, j5])
        assert self.cls._finished == [j1, j3, j4, j5]
        assert self.cls._running == [j2]
        assert self.cls._run_exceptions == {j4: (exc, 'm_traceback')}
        assert mock_poll.mock_calls == [call(self.cls)]
        assert mock_report.mock_calls == [call(self.cls)]
        assert self.config.jobs_for_schedules.mock_calls == []
        assert j1.mock_calls == [call.run()]
        assert j2.mock_calls == [call.run()]
        assert j3.mock_calls == [call.run()]
        assert j4.mock_calls == [call.run()]
        assert j5.mock_calls == []
        assert m_fmt_exc.mock_calls == [call()]

    @freeze_time('2017-10-20 12:30:00')
    def test_run_jobs_timeout(self):

        def se_run():
            self.cls._timeout = datetime(2017, 10, 20, 12, 20, 00)
            return None

        j1 = Mock(name='job1')
        j1.run.return_value = True
        type(j1).skip = PropertyMock(return_value=None)
        j2 = Mock(name='job2')
        j2.run.side_effect = se_run
        type(j2).skip = PropertyMock(return_value=None)
        j3 = Mock(name='job3')
        j3.run.return_value = False
        type(j3).skip = PropertyMock(return_value=None)
        j4 = Mock(name='job4')
        type(j4).error_repr = PropertyMock(return_value='j4erepr')
        exc = RuntimeError('foo')
        j4.run.side_effect = exc
        type(j4).skip = PropertyMock(return_value=None)
        self.config.get_global.return_value = 3600
        self.cls._finished = ['a']
        self.cls._running = ['b']
        self.cls._run_exceptions['foo'] = 6
        with patch('%s._poll_jobs' % pb, autospec=True) as mock_poll:
            with patch('%s._report' % pb, autospec=True) as mock_report:
                with patch('%s.logger' % pbm) as mock_logger:
                    with patch('%s.format_exc' % pbm) as m_fmt_exc:
                        m_fmt_exc.return_value = 'm_traceback'
                        self.cls._run_jobs([j1, j2, j3, j4])
        assert self.cls._finished == [j1]
        assert self.cls._running == [j2, j3, j4]
        assert self.cls._run_exceptions == {}
        assert mock_poll.mock_calls == [call(self.cls)]
        assert mock_report.mock_calls == [call(self.cls)]
        assert self.config.jobs_for_schedules.mock_calls == []
        assert j1.mock_calls == [call.run()]
        assert j2.mock_calls == [call.run()]
        assert j3.mock_calls == []
        assert j4.mock_calls == []
        assert call.error(
            'Time limit reached; not running any more jobs!'
        ) in mock_logger.mock_calls
        assert m_fmt_exc.mock_calls == []

    @freeze_time('2017-10-20 12:30:00')
    def test_poll_jobs(self):
        self.config.get_global.return_value = 3600
        self.cls._timeout = datetime(2017, 10, 20, 13, 30, 00)
        j1 = Mock(name='job1')
        j1.poll.return_value = True
        j2 = Mock(name='job2')
        j2.poll.side_effect = [False, False, True]
        j3 = Mock(name='job3')
        j3.poll.return_value = True
        self.cls._running = [j1, j2, j3]
        self.cls._finished = []
        with patch('%s.sleep' % pbm) as mock_sleep:
            self.cls._poll_jobs()
        assert self.cls._finished == [j1, j3, j2]
        assert self.cls._running == []
        assert j1.mock_calls == [call.poll()]
        assert j2.mock_calls == [call.poll(), call.poll(), call.poll()]
        assert j3.mock_calls == [call.poll()]
        assert mock_sleep.mock_calls == [call(3600), call(3600)]

    @freeze_time('2017-10-20 12:30:00')
    def test_poll_jobs_timeout(self):
        self.poll_num = 0

        def se_poll():
            if self.poll_num == 0:
                self.poll_num = 1
                return False
            self.cls._timeout = datetime(2017, 10, 20, 12, 30, 00)

        self.config.get_global.return_value = 3600
        self.cls._timeout = datetime(2017, 10, 20, 13, 30, 00)
        j1 = Mock(name='job1')
        j1.poll.return_value = True
        j2 = Mock(name='job2')
        j2.poll.side_effect = se_poll
        j3 = Mock(name='job3')
        j3.poll.return_value = True
        self.cls._running = [j1, j2, j3]
        self.cls._finished = []
        with patch('%s.sleep' % pbm) as mock_sleep:
            with patch('%s.logger' % pbm) as mock_logger:
                self.cls._poll_jobs()
        assert self.cls._finished == [j1, j3]
        assert self.cls._running == [j2]
        assert j1.mock_calls == [call.poll()]
        assert j2.mock_calls == [call.poll(), call.poll()]
        assert j3.mock_calls == [call.poll()]
        assert mock_sleep.mock_calls == [call(3600), call(3600)]
        assert call.error(
            'Time limit reached; not polling any more jobs!'
        ) in mock_logger.mock_calls

    @freeze_time('2017-10-20 12:30:00')
    def test_report(self):
        self.cls._finished = Mock()
        self.cls._running = Mock()
        self.cls._run_exceptions = Mock()
        self.cls._start_time = datetime(2017, 10, 20, 11, 45, 00)
        with patch('%s.Reporter' % pbm, autospec=True) as mock_report:
            self.cls._report()
        assert mock_report.mock_calls == [
            call(self.config),
            call().run(
                self.cls._finished,
                self.cls._running,
                self.cls._run_exceptions,
                datetime(2017, 10, 20, 11, 45, 00),
                datetime(2017, 10, 20, 12, 30, 00),
                only_email_if_problems=False
            )
        ]

    @freeze_time('2017-10-20 12:30:00')
    def test_report_only_if_problems(self):
        self.cls._finished = Mock()
        self.cls._running = Mock()
        self.cls._run_exceptions = Mock()
        self.cls._only_email_if_problems = True
        self.cls._start_time = datetime(2017, 10, 20, 11, 45, 00)
        with patch('%s.Reporter' % pbm, autospec=True) as mock_report:
            self.cls._report()
        assert mock_report.mock_calls == [
            call(self.config),
            call().run(
                self.cls._finished,
                self.cls._running,
                self.cls._run_exceptions,
                datetime(2017, 10, 20, 11, 45, 00),
                datetime(2017, 10, 20, 12, 30, 00),
                only_email_if_problems=True
            )
        ]
