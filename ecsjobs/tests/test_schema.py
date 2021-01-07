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
        conf = yaml.load(config_yaml, Loader=yaml.FullLoader)
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
        conf = yaml.load(config_yaml, Loader=yaml.FullLoader)
        with pytest.raises(ValidationError) as exc:
            Schema().validate(conf)
        assert list(exc.value.relative_path) == ['jobs', 0]
        assert exc.value.instance == conf['jobs'][0]
        assert exc.value.validator == 'anyOf'
        assert list(exc.value.relative_schema_path) == [
            'properties', 'jobs', 'items', 'anyOf'
        ]
