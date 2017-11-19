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

from unittest.mock import patch

from ecsjobs.jobs import schema_for_job_class


pbm = 'ecsjobs.jobs'


class FakeJob(object):

    _schema_dict = {
        'type': 'object',
        'title': 'Configuration for base Job class',
        'properties': {
            'name': {'type': 'string'},
            'schedule': {'type': 'string'},
            'class_name': {'type': 'string'}
        },
        'required': [
            'name',
            'schedule',
            'class_name'
        ]
    }


class FakeJobOne(object):

    _schema_dict = {
        'type': 'object',
        'title': 'Configuration for foo',
        'properties': {
            'prop1': {'type': 'string'},
            'prop2': {'type': 'array'}
        }
    }


class FakeJobTwo(object):

    _schema_dict = {
        'type': 'object',
        'title': 'Configuration for bar',
        'properties': {
            'propBar': {'type': 'string'}
        },
        'required': ['propBar']
    }


class TestSchemaForJobs(object):

    def test_one(self):
        jclasses = {
            'FakeJobOne': FakeJobOne,
            'FakeJobTwo': FakeJobTwo
        }
        with patch('%s.get_job_classes' % pbm) as mock_gjc:
            mock_gjc.return_value = jclasses
            with patch('%s.Job' % pbm, FakeJob):
                s = schema_for_job_class(FakeJobOne)
        assert s == {
            'type': 'object',
            'title': 'Configuration for FakeJobOne class instance',
            'properties': {
                'name': {'type': 'string'},
                'schedule': {'type': 'string'},
                'class_name': {'enum': ['FakeJobOne']},
                'prop1': {'type': 'string'},
                'prop2': {'type': 'array'}
            },
            'required': [
                'class_name',
                'name',
                'schedule'
            ]
        }

    def test_two(self):
        jclasses = {
            'FakeJobOne': FakeJobOne,
            'FakeJobTwo': FakeJobTwo
        }
        with patch('%s.get_job_classes' % pbm) as mock_gjc:
            mock_gjc.return_value = jclasses
            with patch('%s.Job' % pbm, FakeJob):
                s = schema_for_job_class(FakeJobTwo)
        assert s == {
            'type': 'object',
            'title': 'Configuration for FakeJobTwo class instance',
            'properties': {
                'name': {'type': 'string'},
                'schedule': {'type': 'string'},
                'class_name': {'enum': ['FakeJobTwo']},
                'propBar': {'type': 'string'}
            },
            'required': [
                'class_name',
                'name',
                'propBar',
                'schedule'
            ]
        }
