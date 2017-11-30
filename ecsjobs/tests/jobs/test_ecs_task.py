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

from unittest.mock import patch, call, Mock
from freezegun import freeze_time
import pytest
from datetime import datetime

from ecsjobs.jobs.ecs_task import EcsTask

pbm = 'ecsjobs.jobs.ecs_task'
pb = '%s.EcsTask' % pbm


class TestEcsTaskInit(object):

    def test_init(self):
        cls = EcsTask(
            'jname', 'sname',
            cluster_name='clname',
            task_definition_family='famname'
        )
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._summary_regex is None
        assert cls._cron_expression is None
        assert cls._cluster_name == 'clname'
        assert cls._family == 'famname'
        assert cls._overrides is None
        assert cls._network_config is None
        assert cls._ecs is None
        assert cls._cw is None
        assert cls._task_arn is None
        assert cls._log_sources is None

    @freeze_time('2017-11-23 12:32:53')
    def test_init_all_options(self):
        mock_cronex = Mock()
        with patch('ecsjobs.jobs.base.CronExpression') as m_cronex:
            m_cronex.return_value = mock_cronex
            cls = EcsTask(
                'jname', 'sname',
                summary_regex='sre',
                cron_expression='crex',
                cluster_name='clname',
                task_definition_family='famname',
                overrides={'foo': 'bar'},
                network_configuration={'baz': 'blam'}
            )
        assert cls.name == 'jname'
        assert cls.schedule_name == 'sname'
        assert cls._summary_regex == 'sre'
        assert cls._cron_expression == mock_cronex
        assert cls._cluster_name == 'clname'
        assert cls._family == 'famname'
        assert cls._overrides == {'foo': 'bar'}
        assert cls._network_config == {'baz': 'blam'}
        assert cls._ecs is None
        assert cls._cw is None
        assert cls._task_arn is None
        assert cls._log_sources is None
        assert m_cronex.mock_calls == [
            call('crex'),
            call().check_trigger((2017, 11, 23, 12, 32))
        ]


class TestEcsTask(object):

    def setup(self):
        self.mock_ecs = Mock()
        self.mock_cw = Mock()
        self.cls = EcsTask(
            'jname', 'sname',
            cluster_name='clname',
            task_definition_family='famname'
        )

    def test_report_description_no_overrides(self):
        assert self.cls.report_description() == 'famname'

    def test_report_description_with_overrides(self):
        self.cls._overrides = {'foo': 'bar'}
        assert self.cls.report_description() == 'famname (with overrides)'

    def test_log_info_for_task(self):
        self.cls._ecs = self.mock_ecs
        self.mock_ecs.describe_task_definition.return_value = {
            'taskDefinition': {
                'containerDefinitions': [
                    {
                        'name': 'baz',
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': 'g1',
                                'awslogs-stream-prefix': 'p1'
                            }
                        }
                    },
                    {
                        'name': 'foo',
                        'logConfiguration': {
                            'logDriver': 'foo'
                        }
                    },
                    {
                        'name': 'bar',
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'foo': 'bar'
                            }
                        }
                    },
                    {
                        'name': 'blam',
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': 'g2',
                                'awslogs-stream-prefix': 'p2'
                            }
                        }
                    }
                ]
            }
        }
        assert self.cls._log_info_for_task('fname') == {
            'baz': ('g1', 'p1'),
            'blam': ('g2', 'p2')
        }
        assert self.mock_ecs.mock_calls == [
            call.describe_task_definition(taskDefinition='fname')
        ]

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_run(self):
        self.mock_ecs.run_task.return_value = {
            'tasks': [
                {
                    'taskArn': 'tarn',
                    'foo': 'bar'
                }
            ]
        }

        def se_client(svcname):
            if svcname == 'ecs':
                return self.mock_ecs
            return self.mock_cw

        with patch('%s.boto3' % pbm) as m_boto:
            m_boto.client.side_effect = se_client
            with patch('%s._log_info_for_task' % pb, autospec=True) as m_lift:
                m_lift.return_value = {'c1': ('g1', 'p1'), 'c2': ('g2', 'p2')}
                res = self.cls.run()
        assert res is None
        assert self.cls._ecs == self.mock_ecs
        assert self.cls._cw == self.mock_cw
        assert self.cls._log_sources == {'c1': ('g1', 'p1'), 'c2': ('g2', 'p2')}
        assert self.cls._started is True
        assert self.cls._start_time == datetime(2017, 10, 20, 12, 30, 00)
        assert self.cls._finished is False
        assert self.cls._task_arn == 'tarn'
        assert m_boto.mock_calls == [
            call.client('ecs'),
            call.client('logs')
        ]
        assert self.mock_ecs.mock_calls == [
            call.run_task(
                cluster='clname',
                taskDefinition='famname',
                count=1
            )
        ]
        assert m_lift.mock_calls == [
            call(self.cls, 'famname')
        ]

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_run_overrides(self):
        self.mock_ecs.run_task.return_value = {
            'tasks': [
                {
                    'taskArn': 'tarn',
                    'foo': 'bar'
                }
            ]
        }
        self.cls._overrides = {'foo': 'bar'}
        self.cls._network_config = {'baz': 'blam'}

        def se_client(svcname):
            if svcname == 'ecs':
                return self.mock_ecs
            return self.mock_cw

        with patch('%s.boto3' % pbm) as m_boto:
            m_boto.client.side_effect = se_client
            with patch('%s._log_info_for_task' % pb, autospec=True) as m_lift:
                m_lift.return_value = {'c1': ('g1', 'p1'), 'c2': ('g2', 'p2')}
                res = self.cls.run()
        assert res is None
        assert self.cls._ecs == self.mock_ecs
        assert self.cls._cw == self.mock_cw
        assert self.cls._log_sources == {'c1': ('g1', 'p1'), 'c2': ('g2', 'p2')}
        assert self.cls._started is True
        assert self.cls._start_time == datetime(2017, 10, 20, 12, 30, 00)
        assert self.cls._finished is False
        assert self.cls._task_arn == 'tarn'
        assert m_boto.mock_calls == [
            call.client('ecs'),
            call.client('logs')
        ]
        assert self.mock_ecs.mock_calls == [
            call.run_task(
                cluster='clname',
                taskDefinition='famname',
                count=1,
                overrides={'foo': 'bar'},
                networkConfiguration={'baz': 'blam'}
            )
        ]
        assert m_lift.mock_calls == [
            call(self.cls, 'famname')
        ]

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_poll_finished_logs(self):
        self.cls._task_arn = 'arn::task/task-id'
        self.cls._log_sources = {'contname': ('g1', 'p1')}
        self.cls._ecs = self.mock_ecs
        self.mock_ecs.describe_tasks.return_value = {
            "failures": [],
            "tasks": [
                {
                    "taskArn": self.cls._task_arn,
                    "group": "family:famname",
                    "overrides": {},
                    "lastStatus": "STOPPED",
                    "containerInstanceArn": "c_i_arn",
                    "createdAt": 1511997624.585,
                    "version": 3,
                    "clusterArn": "cluster_arn",
                    "startedAt": 1511997628.724,
                    "desiredStatus": "STOPPED",
                    "stoppedReason": "Essential container in task exited",
                    "taskDefinitionArn": "td_arn",
                    "containers": [
                        {
                            "containerArn": "arn:container/cont_id",
                            "taskArn": self.cls._task_arn,
                            "name": "contname",
                            "networkBindings": [],
                            "lastStatus": "STOPPED",
                            "exitCode": 3
                        },
                        {
                            "containerArn": "arn:container/cont2_id",
                            "taskArn": self.cls._task_arn,
                            "name": "cont2name",
                            "networkBindings": [],
                            "lastStatus": "STOPPED",
                            "exitCode": 0
                        },
                        {
                            "containerArn": "arn:container/cont3_id",
                            "taskArn": self.cls._task_arn,
                            "name": "cont3name",
                            "networkBindings": [],
                            "lastStatus": "STOPPED",
                            "exitCode": 0
                        }
                    ],
                    "stoppedAt": 1511997628.878
                }
            ]
        }

        def se_oftc(_, taskid, cname):
            if cname == 'cont2name':
                raise RuntimeError('foo')
            return '%s-%s-output' % (taskid, cname)

        with patch(
            '%s._output_for_task_container' % pb, autospec=True
        ) as m_oftc:
            m_oftc.side_effect = se_oftc
            res = self.cls.poll()
        assert res is True
        assert self.cls._finished is True
        assert self.cls._finish_time == datetime(2017, 10, 20, 12, 30, 00)
        assert self.cls._exit_code == 3
        assert self.cls._output == 'Output for container "contname" ' \
                                   '(exitCode 3)\n' \
                                   'task-id-contname-output\n' \
                                   'Output for container "cont2name" ' \
                                   '(exitCode 0)\n' \
                                   'Exception getting output: RuntimeError: ' \
                                   'foo\n' \
                                   'Output for container "cont3name" ' \
                                   '(exitCode 0)\n' \
                                   'task-id-cont3name-output\n'
        assert self.mock_ecs.mock_calls == [
            call.describe_tasks(cluster='clname', tasks=[self.cls._task_arn])
        ]
        assert m_oftc.mock_calls == [
            call(self.cls, 'task-id', 'contname'),
            call(self.cls, 'task-id', 'cont2name'),
            call(self.cls, 'task-id', 'cont3name')
        ]

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_poll_exception(self):
        self.cls._task_arn = 'arn::task/task-id'
        self.cls._log_sources = {'contname': ('g1', 'p1')}
        self.cls._ecs = self.mock_ecs
        self.mock_ecs.describe_tasks.side_effect = RuntimeError('foo')

        def se_oftc(_, taskid, cname):
            return '%s-%s-output' % (taskid, cname)

        with patch(
            '%s._output_for_task_container' % pb, autospec=True
        ) as m_oftc:
            m_oftc.side_effect = se_oftc
            res = self.cls.poll()
        assert res is False
        assert self.cls._finished is False
        assert self.cls._finish_time is None
        assert self.cls._exit_code is None
        assert self.cls._output is None
        assert self.mock_ecs.mock_calls == [
            call.describe_tasks(cluster='clname', tasks=[self.cls._task_arn])
        ]
        assert m_oftc.mock_calls == []

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_poll_running(self):
        self.cls._task_arn = 'arn::task/task-id'
        self.cls._log_sources = {'contname': ('g1', 'p1')}
        self.cls._ecs = self.mock_ecs
        self.mock_ecs.describe_tasks.return_value = {
            "failures": [],
            "tasks": [
                {
                    "taskArn": self.cls._task_arn,
                    "group": "family:famname",
                    "overrides": {},
                    "lastStatus": "RUNNING",
                    "containerInstanceArn": "c_i_arn",
                    "createdAt": 1511997624.585,
                    "version": 3,
                    "clusterArn": "cluster_arn",
                    "startedAt": 1511997628.724,
                    "desiredStatus": "RUNNING",
                    "stoppedReason": "Essential container in task exited",
                    "taskDefinitionArn": "td_arn",
                    "containers": [
                        {
                            "containerArn": "arn:container/cont_id",
                            "taskArn": self.cls._task_arn,
                            "name": "contname",
                            "networkBindings": [],
                            "lastStatus": "RUNNING"
                        }
                    ],
                    "stoppedAt": 1511997628.878
                }
            ]
        }

        def se_oftc(_, taskid, cname):
            return '%s-%s-output' % (taskid, cname)

        with patch(
            '%s._output_for_task_container' % pb, autospec=True
        ) as m_oftc:
            m_oftc.side_effect = se_oftc
            res = self.cls.poll()
        assert res is False
        assert self.cls._finished is False
        assert self.cls._finish_time is None
        assert self.cls._exit_code is None
        assert self.cls._output is None
        assert self.mock_ecs.mock_calls == [
            call.describe_tasks(cluster='clname', tasks=[self.cls._task_arn])
        ]
        assert m_oftc.mock_calls == []

    @freeze_time(datetime(2017, 10, 20, 12, 30, 00))
    def test_poll_finished_no_logs(self):
        self.cls._task_arn = 'arn::task/task-id'
        self.cls._log_sources = {}
        self.cls._ecs = self.mock_ecs
        self.mock_ecs.describe_tasks.return_value = {
            "failures": [],
            "tasks": [
                {
                    "taskArn": self.cls._task_arn,
                    "group": "family:famname",
                    "overrides": {},
                    "lastStatus": "STOPPED",
                    "containerInstanceArn": "c_i_arn",
                    "createdAt": 1511997624.585,
                    "version": 3,
                    "clusterArn": "cluster_arn",
                    "startedAt": 1511997628.724,
                    "desiredStatus": "STOPPED",
                    "stoppedReason": "Essential container in task exited",
                    "taskDefinitionArn": "td_arn",
                    "containers": [
                        {
                            "containerArn": "arn:container/cont_id",
                            "taskArn": self.cls._task_arn,
                            "name": "contname",
                            "networkBindings": [],
                            "lastStatus": "STOPPED",
                            "exitCode": 3
                        }
                    ],
                    "stoppedAt": 1511997628.878
                }
            ]
        }

        def se_oftc(_, taskid, cname):
            return '%s-%s-output' % (taskid, cname)

        with patch(
            '%s._output_for_task_container' % pb, autospec=True
        ) as m_oftc:
            m_oftc.side_effect = se_oftc
            res = self.cls.poll()
        assert res is True
        assert self.cls._finished is True
        assert self.cls._finish_time == datetime(2017, 10, 20, 12, 30, 00)
        assert self.cls._exit_code == 3
        assert self.cls._output == 'No output available for Task task-id ' \
                                   'containers:\n' \
                                   'contname cont_id (exit code 3)\n'
        assert self.mock_ecs.mock_calls == [
            call.describe_tasks(cluster='clname', tasks=[self.cls._task_arn])
        ]
        assert m_oftc.mock_calls == []

    def test_output_for_container(self):
        self.cls._log_sources = {'cname': ('grpname', 'sprefix')}
        m_paginator = Mock()
        m_paginator.paginate.return_value = [
            {
                'events': [
                    {
                        'timestamp': 1512005266000,
                        'message': 'msg1'
                    },
                    {
                        'timestamp': 1512005267000,
                        'message': 'msg2'
                    },
                    {
                        'timestamp': 1512005268000,
                        'message': 'msg3'
                    }
                ]
            },
            {
                'events': [
                    {
                        'timestamp': 1512005269000,
                        'message': 'msg4'
                    },
                    {
                        'timestamp': 1512005269000,
                        'message': 'msg5'
                    }
                ]
            }
        ]
        self.mock_cw.get_paginator.return_value = m_paginator
        self.cls._cw = self.mock_cw
        res = self.cls._output_for_task_container('tid', 'cname')
        assert res == '2017-11-30 01:27:46Z\tmsg1\n' \
                      '2017-11-30 01:27:47Z\tmsg2\n' \
                      '2017-11-30 01:27:48Z\tmsg3\n' \
                      '2017-11-30 01:27:49Z\tmsg4\n' \
                      '2017-11-30 01:27:49Z\tmsg5\n'
        assert self.mock_cw.mock_calls == [
            call.get_paginator('filter_log_events'),
            call.get_paginator().paginate(
                logGroupName='grpname',
                logStreamNames=['sprefix/cname/tid']
            )
        ]

    def test_output_for_container_exception(self):
        self.cls._log_sources = {'NOTcname': ('grpname', 'sprefix')}
        self.cls._cw = self.mock_cw
        with pytest.raises(RuntimeError) as exc:
            self.cls._output_for_task_container('tid', 'cname')
        assert str(exc.value) == 'No log configuration found for task ' \
                                 'tid container cname'
        assert self.mock_cw.mock_calls == []
