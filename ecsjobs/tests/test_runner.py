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

from unittest.mock import patch, call, Mock, DEFAULT, PropertyMock

from ecsjobs.runner import (
    set_log_debug, set_log_info, set_log_level_format, parse_args, main
)
from ecsjobs.version import VERSION, PROJECT_URL

pbm = 'ecsjobs.runner'


class MockArgs(object):

    def __init__(self, **kwargs):
        self.verbose = 0
        self.ACTION = None
        self.SCHEDULES = []
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestParseArgs(object):

    def test_parse_args_list_schedules(self):
        res = parse_args(['-v', 'list-schedules'])
        assert res.verbose == 1
        assert res.ACTION == 'list-schedules'
        assert res.SCHEDULES == []

    def test_parse_args_validate(self):
        res = parse_args(['-vv', 'validate'])
        assert res.verbose == 2
        assert res.ACTION == 'validate'
        assert res.SCHEDULES == []

    def test_parse_args_run_none(self):
        with pytest.raises(RuntimeError) as exc:
            parse_args(['run'])
        assert str(exc.value) == 'ERROR: "run" action must have one or ' \
                                 'more SCHEDULES specified'

    def test_parse_args_run_one(self):
        res = parse_args(['run', 'foo'])
        assert res.verbose == 0
        assert res.ACTION == 'run'
        assert res.SCHEDULES == ['foo']

    def test_parse_args_run_three(self):
        res = parse_args(['-v', 'run', 'foo', 'bar', 'baz'])
        assert res.verbose == 1
        assert res.ACTION == 'run'
        assert res.SCHEDULES == ['foo', 'bar', 'baz']

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
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_BUCKET': 'bname', 'ECSJOBS_KEY': 'keyname'},
                clear=True
            ):
                with patch('%s.sys.argv' % pbm, ['foo', '-V']):
                    with pytest.raises(SystemExit):
                        main()
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['-V'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == []
        assert mocks['EcsJobsRunner'].mock_calls == []

    def test_info_no_bucket(self):
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
            mocks['parse_args'].return_value = MockArgs(verbose=1)
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_KEY': 'keyname'},
                clear=True
            ):
                with pytest.raises(RuntimeError) as exc:
                    main(['foo'])
        assert str(exc.value) == 'ERROR: You must set "ECSJOBS_BUCKET" ' \
                                 'environment variable.'
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['foo'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == [call(logging.getLogger())]
        assert mocks['Config'].mock_calls == []
        assert mocks['EcsJobsRunner'].mock_calls == []

    def test_debug_no_key(self):
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
            mocks['parse_args'].return_value = MockArgs(verbose=2, ACTION='run')
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_BUCKET': 'bname'},
                clear=True
            ):
                with pytest.raises(RuntimeError) as exc:
                    main(['foo'])
        assert str(exc.value) == 'ERROR: You must set "ECSJOBS_KEY" ' \
                                 'environment variable.'
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['foo'])]
        assert mocks['set_log_debug'].mock_calls == [call(logging.getLogger())]
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
            mocks['parse_args'].return_value = MockArgs(ACTION='validate')
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_BUCKET': 'bname', 'ECSJOBS_KEY': 'keyname'},
                clear=True
            ):
                with pytest.raises(SystemExit) as exc:
                    main(['validate'])
        assert exc.value.code == 0
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['validate'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == [
            call('bname', 'keyname')
        ]
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
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_BUCKET': 'bname', 'ECSJOBS_KEY': 'keyname'},
                clear=True
            ):
                with pytest.raises(SystemExit) as exc:
                    main(['list-schedules'])
        assert exc.value.code == 0
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['list-schedules'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == [
            call('bname', 'keyname')
        ]
        assert mocks['EcsJobsRunner'].mock_calls == []
        out, err = capsys.readouterr()
        assert err == ''
        assert out == "foo\nbar\nbaz\n"

    def test_run(self, capsys):
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
                ACTION='run', SCHEDULES=['foo', 'baz']
            )
            with patch.dict(
                '%s.os.environ' % pbm,
                {'ECSJOBS_BUCKET': 'bname', 'ECSJOBS_KEY': 'keyname'},
                clear=True
            ):
                main(['run', 'foo', 'baz'])
        assert mocks['logger'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['run', 'foo', 'baz'])]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['Config'].mock_calls == [
            call('bname', 'keyname')
        ]
        assert mocks['EcsJobsRunner'].mock_calls == [
            call(mocks['Config'].return_value),
            call().run_schedules(['foo', 'baz'])
        ]
