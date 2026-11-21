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

from copy import deepcopy
from unittest.mock import patch, call
from textwrap import dedent
import yaml
from jsonschema import ValidationError
import pytest

from ecsjobs.schema import Schema

pbm = 'ecsjobs.schema'
pb = 'ecsjobs.schema.Schema'


class TestSchemaInit(object):

    def test_schema_init(self):

        def se_schema_for_job_class(cls):
            return {'title': 'Schema for %s' % cls}

        jclasses = {
            'Foo': 'FooClass',
            'Bar': 'BarClass'
        }
        expected = deepcopy(Schema.base_schema)
        expected['definitions'] = {
            'Foo': {'title': 'Schema for FooClass'},
            'Bar': {'title': 'Schema for BarClass'}
        }
        expected['properties']['jobs']['items']['anyOf'] = [
            {'$ref': '#/definitions/Bar'},
            {'$ref': '#/definitions/Foo'}
        ]
        with patch('%s.get_job_classes' % pbm) as mock_gjc:
            mock_gjc.return_value = jclasses
            with patch('%s.schema_for_job_class' % pbm) as m_sfjc:
                m_sfjc.side_effect = se_schema_for_job_class
                res = Schema().schema_dict
        assert res == expected


class TestValidate(object):

    def test_validate_ok(self):
        with patch('%s.jsonschema.validate' % pbm) as mock_v:
            mock_v.return_value = None
            s = Schema()
            s.validate({'jobs': [{'name': 'foo'}]})
        assert mock_v.mock_calls == [
            call({'jobs': [{'name': 'foo'}]}, s.schema_dict)
        ]

    def test_validate_dupe_jobs(self):
        conf = {'jobs': [
            {'name': 'foo'},
            {'name': 'bar'},
            {'name': 'foo'}
        ]}
        with patch('%s.jsonschema.validate' % pbm) as mock_v:
            mock_v.return_value = None
            s = Schema()
            with pytest.raises(RuntimeError) as exc:
                s.validate(conf)
            assert str(exc.value) == "ERROR: Duplicate Job names in " \
                                     "configuration: ['foo']"
        assert mock_v.mock_calls == [
            call(conf, s.schema_dict)
        ]


class TestValidateExamples(object):

    def test_simple_success(self):
        config_yaml = dedent("""
        global:
          from_email: you@example.com
          to_email:
            - target@example.com
        jobs:
        - name: jobOne
          class_name: DockerExec
          schedule: foo
          container_name: myCont
          command: /my/command
        - name: jobTwo
          class_name: LocalCommand
          schedule: foo
          command: uptime
        """)
        conf = yaml.safe_load(config_yaml)
        Schema().validate(conf)

    def test_local_command_missing_schedule(self):
        config_yaml = dedent("""
        global:
          from_email: you@example.com
          to_email:
            - target@example.com
        jobs:
        - name: jobOne
          class_name: DockerExec
          container_name: myCont
          command: /my/command
        - name: jobTwo
          class_name: LocalCommand
          schedule: foo
        """)
        conf = yaml.safe_load(config_yaml)
        with pytest.raises(ValidationError) as exc:
            Schema().validate(conf)
        assert list(exc.value.relative_path) == ['jobs', 0]
        assert exc.value.instance == conf['jobs'][0]
        assert exc.value.validator == 'anyOf'
        assert list(exc.value.relative_schema_path) == [
            'properties', 'jobs', 'items', 'anyOf'
        ]


class TestCommandArrayItems(object):
    """The ``command`` array must contain only strings (every element)."""

    @staticmethod
    def _conf(class_name, command):
        job = {
            'name': 'jobOne',
            'class_name': class_name,
            'schedule': 'foo',
            'command': command
        }
        if class_name == 'DockerExec':
            job['container_name'] = 'myCont'
        if class_name == 'EcsDockerExec':
            job['container_name'] = 'myCont'
        return {
            'global': {
                'from_email': 'you@example.com',
                'to_email': ['target@example.com']
            },
            'jobs': [job]
        }

    @pytest.mark.parametrize(
        'class_name', ['LocalCommand', 'DockerExec', 'EcsDockerExec']
    )
    def test_all_string_array_accepted(self, class_name):
        Schema().validate(self._conf(class_name, ['ls', '-l', '/tmp']))

    @pytest.mark.parametrize(
        'class_name', ['LocalCommand', 'DockerExec', 'EcsDockerExec']
    )
    @pytest.mark.parametrize(
        'command', [['ls', 1], ['ls', '-l', None], ['ls', ['a']]]
    )
    def test_non_string_array_element_rejected(self, class_name, command):
        with pytest.raises(ValidationError):
            Schema().validate(self._conf(class_name, command))


GLOBAL_CONF = {
    'from_email': 'you@example.com',
    'to_email': ['target@example.com']
}

# every documented property of each job class, with representative values
FULL_JOBS = {
    'LocalCommand': {
        'command': ['/bin/echo', 'foo'],
        'shell': False,
        'timeout': 30,
        'script_source': 'https://example.com/script.sh'
    },
    'DockerExec': {
        'container_name': 'myCont',
        'command': ['ls', '-l'],
        'tty': False,
        'stdout': True,
        'stderr': True,
        'privileged': False,
        'user': 'root',
        'environment': {'FOO': 'bar'}
    },
    'EcsDockerExec': {
        'task_definition_family': 'myFamily',
        'container_name': 'myCont',
        'command': 'ls -l',
        'tty': False,
        'stdout': True,
        'stderr': True,
        'privileged': False,
        'user': 'root',
        'environment': ['FOO=bar']
    },
    'EcsTask': {
        'cluster_name': 'myCluster',
        'task_definition_family': 'myFamily',
        'overrides': {'containerOverrides': []},
        'network_configuration': {'awsvpcConfiguration': {}}
    },
}


class TestStrictKeys(object):
    """Unknown keys are errors in the global section and in every job."""

    @staticmethod
    def _job(class_name):
        job = {
            'name': 'jobOne',
            'class_name': class_name,
            'schedule': 'foo',
            'summary_regex': 'x(.*)',
            'cron_expression': '0 * * * *'
        }
        job.update(FULL_JOBS[class_name])
        return job

    @pytest.mark.parametrize('class_name', sorted(FULL_JOBS))
    def test_all_documented_properties_valid(self, class_name):
        conf = {
            'global': dict(
                GLOBAL_CONF,
                inter_poll_sleep_sec=5,
                max_total_runtime_sec=600,
                email_subject='Subj',
                failure_html_path='/tmp/fail-{date}.html',
                failure_command=['/bin/cat', '-n']
            ),
            'jobs': [self._job(class_name)]
        }
        Schema().validate(conf)

    @pytest.mark.parametrize('class_name', sorted(FULL_JOBS))
    def test_unknown_job_key_rejected(self, class_name):
        job = self._job(class_name)
        job['shel'] = True
        with pytest.raises(ValidationError):
            Schema().validate({'global': GLOBAL_CONF, 'jobs': [job]})

    def test_misspelled_local_command_key_rejected(self):
        job = {
            'name': 'jobOne',
            'class_name': 'LocalCommand',
            'schedule': 'foo',
            'command': 'uptime',
            'shel': True
        }
        with pytest.raises(ValidationError):
            Schema().validate({'global': GLOBAL_CONF, 'jobs': [job]})

    def test_unknown_global_key_rejected(self):
        conf = {
            'global': dict(GLOBAL_CONF),
            'jobs': []
        }
        conf['global']['bogus_key'] = 1
        with pytest.raises(ValidationError) as exc:
            Schema().validate(conf)
        assert exc.value.validator == 'additionalProperties'
        assert list(exc.value.relative_path) == ['global']

    def test_failure_command_requires_strings(self):
        conf = {
            'global': dict(GLOBAL_CONF, failure_command=['/bin/cat', 1]),
            'jobs': []
        }
        with pytest.raises(ValidationError):
            Schema().validate(conf)
