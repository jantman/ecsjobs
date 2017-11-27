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

from unittest.mock import patch, call, MagicMock, Mock, PropertyMock
from datetime import datetime

from freezegun import freeze_time
import pytest
from ecsjobs.jobs.docker_exec_mixin import DockerExecMixin

pbm = 'ecsjobs.jobs.docker_exec_mixin'
pb = '%s.DockerExecMixin' % pbm


class TestDockerExecMixin(object):

    def setup(self):
        self.cls = DockerExecMixin()
        self.m_docker = MagicMock()
        self.m_container = Mock()
        type(self.m_container).short_id = PropertyMock(return_value='cid')
        type(self.m_container).id = PropertyMock(return_value='longcid')
        self.cls._docker = self.m_docker

    def test_defaults(self):
        self.frozen = None
        self.second_dt = datetime(2017, 10, 20, 12, 35, 00)

        self.cls._container_name = 'cname'
        self.cls._command = '/my/cmd'
        self.cls._stdout = True
        self.cls._stderr = True
        self.cls._tty = False
        self.cls._privileged = False
        self.cls._user = 'root'
        self.cls._environment = None

        def se_create(*args, **kwargs):
            self.frozen.move_to(self.second_dt)
            return {'Id': 'execid'}

        self.m_docker.containers.get.return_value = self.m_container
        self.m_docker.api.exec_create.side_effect = se_create
        self.m_docker.api.exec_start.return_value = b'foobar'
        self.m_docker.api.exec_inspect.return_value = {
            'Pid': 1234,
            'ExitCode': 3
        }

        initial_dt = datetime(2017, 10, 20, 12, 30, 00)
        with freeze_time(initial_dt) as frozen:
            self.frozen = frozen
            with patch('%s.docker.from_env' % pbm) as m_from_env:
                m_from_env.return_value = self.m_docker
                self.cls._docker_run()

        assert self.cls._container == self.m_container
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._output == 'foobar'
        assert self.cls._exit_code == 3
        assert self.cls._finished is True
        assert self.cls._finish_time == self.second_dt

        assert m_from_env.mock_calls == [
            call(),
            call().ping(),
            call().containers.get('cname'),
            call().api.exec_create(
                'longcid', '/my/cmd', stdout=True, stderr=True, tty=False,
                privileged=False, user='root', environment=None
            ),
            call().api.exec_start('execid', tty=False),
            call().api.exec_inspect('execid')
        ]

    def test_non_defaults(self):
        self.frozen = None
        self.second_dt = datetime(2017, 10, 20, 12, 35, 00)

        self.cls._container_name = 'cname'
        self.cls._command = '/my/cmd'
        self.cls._stdout = False
        self.cls._stderr = False
        self.cls._tty = True
        self.cls._privileged = True
        self.cls._user = 'uname'
        self.cls._environment = ['ENV=var']

        def se_create(*args, **kwargs):
            self.frozen.move_to(self.second_dt)
            return {'Id': 'execid'}

        self.m_docker.containers.get.return_value = self.m_container
        self.m_docker.api.exec_create.side_effect = se_create
        self.m_docker.api.exec_start.return_value = b'foobar'
        self.m_docker.api.exec_inspect.return_value = {
            'Pid': 1234,
            'ExitCode': 3
        }

        initial_dt = datetime(2017, 10, 20, 12, 30, 00)
        with freeze_time(initial_dt) as frozen:
            self.frozen = frozen
            with patch('%s.docker.from_env' % pbm) as m_from_env:
                m_from_env.return_value = self.m_docker
                self.cls._docker_run()

        assert self.cls._container == self.m_container
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._output == 'foobar'
        assert self.cls._exit_code == 3
        assert self.cls._finished is True
        assert self.cls._finish_time == self.second_dt

        assert m_from_env.mock_calls == [
            call(),
            call().ping(),
            call().containers.get('cname'),
            call().api.exec_create(
                'longcid', '/my/cmd', stdout=False, stderr=False, tty=True,
                privileged=True, user='uname', environment=['ENV=var']
            ),
            call().api.exec_start('execid', tty=True),
            call().api.exec_inspect('execid')
        ]

    def test_create_exception(self):
        self.frozen = None
        self.second_dt = datetime(2017, 10, 20, 12, 35, 00)

        self.cls._container_name = 'cname'
        self.cls._command = '/my/cmd'
        self.cls._stdout = True
        self.cls._stderr = True
        self.cls._tty = False
        self.cls._privileged = False
        self.cls._user = 'root'
        self.cls._environment = None
        self.cls._output = None
        self.cls._exit_code = None

        def se_create(*args, **kwargs):
            self.frozen.move_to(self.second_dt)
            raise RuntimeError('foo')

        self.m_docker.containers.get.return_value = self.m_container
        self.m_docker.api.exec_create.side_effect = se_create
        self.m_docker.api.exec_start.return_value = b'foobar'
        self.m_docker.api.exec_inspect.return_value = {
            'Pid': 1234,
            'ExitCode': 3
        }

        initial_dt = datetime(2017, 10, 20, 12, 30, 00)
        with freeze_time(initial_dt) as frozen:
            self.frozen = frozen
            with patch('%s.docker.from_env' % pbm) as m_from_env:
                m_from_env.return_value = self.m_docker
                with pytest.raises(RuntimeError):
                    self.cls._docker_run()

        assert self.cls._container == self.m_container
        assert self.cls._started is True
        assert self.cls._start_time == initial_dt
        assert self.cls._output is None
        assert self.cls._exit_code is None
        assert self.cls._finished is True
        assert self.cls._finish_time == self.second_dt

        assert m_from_env.mock_calls == [
            call(),
            call().ping(),
            call().containers.get('cname'),
            call().api.exec_create(
                'longcid', '/my/cmd', stdout=True, stderr=True, tty=False,
                privileged=False, user='root', environment=None
            )
        ]
