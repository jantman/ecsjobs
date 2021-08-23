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

import abc  # noqa
from ecsjobs.jobs.base import Job
import logging
import boto3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EcsTask(Job):
    """
    Class to run an ECS Task asynchronously; starts the task with the
    :py:meth:`~.run` method and then uses :py:meth:`~.poll` to wait for it to
    finish. Sets :py:attr:`~.exitcode` according to:

    - if only one container in the task, the exit code of that container
    - otherwise, the maximum exit code of all containers
    """

    #: Dictionary describing the configuration file schema, to be validated
    #: with `jsonschema <https://github.com/Julian/jsonschema>`_.
    _schema_dict = {
        'type': 'object',
        'properties': {
            'cluster_name': {'type': 'string'},
            'task_definition_family': {
                'type': 'string'
            },
            'overrides': {'type': 'object'},
            'network_configuration': {'type': 'object'}
        },
        'required': [
            'cluster_name',
            'task_definition_family'
        ]
    }

    def __init__(self, name, schedule, summary_regex=None,
                 cron_expression=None, cluster_name=None,
                 task_definition_family=None, overrides=None,
                 network_configuration=None):
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
        :param cluster_name: name of the ECS cluster to run the task on
        :type cluster_name: str
        :param task_definition_family: Name of the Task Definition family to run
        :type task_definition_family: str
        :param overrides: RunTask overrides hash/mapping/dict to pass to ECS
          RunTask API call, as specified in the documentation for
          :py:meth:`ECS.Client.run_task`
        :type overrides: dict
        :param networkConfiguration: RunTask networkConfiguration parameter to
          pass to ECS API call, as specified in the documentation for
          :py:meth:`ECS.Client.run_task`
        :type networkConfiguration: dict
        """
        super(EcsTask, self).__init__(
            name, schedule, summary_regex=summary_regex,
            cron_expression=cron_expression
        )
        self._cluster_name = cluster_name
        assert cluster_name is not None
        self._family = task_definition_family
        assert task_definition_family is not None
        self._overrides = overrides
        self._network_config = network_configuration
        self._ecs = None
        self._cw = None
        self._task_arn = None
        self._log_sources = None

    def run(self):
        """
        Run the command for the job. Output and exit code will be captured by
        :py:meth:`~.poll`, according to ``self._task_id``.

        :return: ``None``
        """
        logger.debug('Connecting to ECS')
        self._ecs = boto3.client('ecs')
        self._cw = boto3.client('logs')
        self._log_sources = self._log_info_for_task(self._family)
        self._started = True
        self._start_time = datetime.now()
        logger.info(
            'Running ECS Task cluster=%s taskDefinition=%s count=1 '
            'overrides=%s networkConfiguration=%s', self._cluster_name,
            self._family, self._overrides, self._network_config
        )
        run_kwargs = {
            'cluster': self._cluster_name,
            'taskDefinition': self._family,
            'count': 1
        }
        if self._overrides is not None:
            run_kwargs['overrides'] = self._overrides
        if self._network_config is not None:
            run_kwargs['networkConfiguration'] = self._network_config
        res = self._ecs.run_task(**run_kwargs)
        logger.debug('RunTask response: %s', res)
        self._task_arn = res['tasks'][0]['taskArn']
        logger.info('Started task %s', self._task_arn)

    def _log_info_for_task(self, task_family):
        """
        Return a dictionary of container name to 2-tuple of Log Group Name and
        Log Stream Prefix, for each container in the specified Task Definition
        that uses the ``awslogs`` log driver.

        :param task_family: task family name to return log settings for
        :type task_family: str
        :return: dictionary of container name to 2-tuple of Log Group Name and
          Log Stream Prefix, for each container in the specified Task Definition
          that uses the ``awslogs`` log driver
        :rtype: dict
        """
        res = {}
        logger.debug('Describing Task Definition %s', task_family)
        task = self._ecs.describe_task_definition(
            taskDefinition=task_family
        )['taskDefinition']
        logger.debug(
            'Task Definition has %d containers',
            len(task['containerDefinitions'])
        )
        for c in task['containerDefinitions']:
            if c['logConfiguration']['logDriver'] != 'awslogs':
                logger.debug('Container %s uses logDriver %s', c['name'],
                             c['logConfiguration']['logDriver'])
                continue
            opts = c['logConfiguration'].get('options', {})
            if 'awslogs-group' in opts and 'awslogs-stream-prefix' in opts:
                res[c['name']] = (
                    opts['awslogs-group'], opts['awslogs-stream-prefix']
                )
        return res

    def report_description(self):
        """
        Return a one-line description of the Job for use in reports.

        :rtype: str
        """
        if self._overrides is not None:
            return '%s (with overrides)' % self._family
        return self._family

    def poll(self):
        """
        Poll to check status on the task. If STOPPED, set this Job as finished
        and collect report information.

        :return: whether or not the Task is finished
        :rtype: bool
        """
        taskid = self._task_arn.split('/')[-1]
        try:
            logger.debug('Calling DescribeTasks for task %s', self._task_arn)
            res = self._ecs.describe_tasks(
                cluster=self._cluster_name, tasks=[self._task_arn]
            )
        except Exception:
            logger.warning('Exception describing Task %s', self._task_arn,
                           exc_info=True)
            return False
        task = res['tasks'][0]
        if task['lastStatus'] != 'STOPPED':
            logger.info('Task %s status: %s', taskid, task['lastStatus'])
            return False
        self._finished = True
        logger.info('Task %s is now STOPPED', taskid)
        self._finish_time = datetime.now()
        ecodes = {c['name']: c['exitCode'] for c in task['containers']}
        self._exit_code = max(ecodes.values())
        logger.info('Task container exit codes: %s', ecodes)
        self._output = ''
        if len(self._log_sources) == 0:
            self._output += 'No output available for Task %s containers:' \
                            '\n' % taskid
            for c in task['containers']:
                self._output += '%s %s (exit code %s)\n' % (
                    c['name'], c['containerArn'].split('/')[-1], c['exitCode']
                )
            return True
        # else we have log sources
        for c in task['containers']:
            try:
                self._output += 'Output for container "%s" (exitCode %s)\n' % (
                    c['name'], c['exitCode']
                )
                self._output += self._output_for_task_container(
                    taskid, c['name']
                ) + "\n"
            except Exception as exc:
                logger.warning('Exception getting CloudWatch logs for task %s'
                               'container %s', taskid, c['name'], exc_info=True)
                self._output += 'Exception getting output: %s: %s\n' % (
                    exc.__class__.__name__, exc
                )
        return True

    def _output_for_task_container(self, taskid, cont_name):
        """
        Update ``self.output`` with the CloudWatch logs for the containers in
        the task.

        :param taskid: ECS Task ID
        :type taskid: str
        :param cont_name: container name in the task
        :type cont_name: str
        :returns: CloudWatch logs for the container
        :rtype: str
        """
        if cont_name not in self._log_sources:
            raise RuntimeError(
                'No log configuration found for task %s container %s' % (
                    taskid, cont_name
                )
            )
        srcinfo = self._log_sources[cont_name]
        stream_name = '%s/%s/%s' % (srcinfo[1], cont_name, taskid)
        logger.debug(
            'Getting logs for taskid=%s container_name=%s from logGroupName=%s '
            'logStreamName=%s', taskid, cont_name, srcinfo[0], stream_name
        )
        res = ''
        paginator = self._cw.get_paginator('filter_log_events')
        for resp_iter in paginator.paginate(
            logGroupName=srcinfo[0], logStreamNames=[stream_name]
        ):
            for evt in resp_iter['events']:
                res += '%sZ\t%s\n' % (
                    datetime.fromtimestamp(
                        evt['timestamp'] / 1000, tz=timezone.utc
                    ).strftime('%Y-%m-%d %H:%M:%S'),
                    evt['message']
                )
        return res
