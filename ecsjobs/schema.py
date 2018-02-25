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
import collections

import jsonschema
from ecsjobs.jobs import get_job_classes, schema_for_job_class


class Schema(object):

    base_schema = {
        '$schema': 'http://json-schema.org/schema#',
        'id': 'http://schemas.jasonantman.com/github/ecsjobs/config.json',
        'title': 'ECSJobs configuration schema',
        'description': 'Overall ecsjobs (Python package) configuration',
        'definitions': {},
        'type': 'object',
        'required': ['global', 'jobs'],
        'additionalProperties': False,
        'properties': {
            'jobs': {
                'type': 'array',
                'additionalItems': False,
                'items': {'anyOf': []},
                'title': 'Array of Jobs to run',
                'description': 'Array of items that construct Job subclass '
                               'instances'
            },
            'global': {
                'type': 'object',
                'title': 'Global configuration for application',
                'additionalItems': False,
                'required': ['from_email', 'to_email'],
                'properties': {
                    'from_email': {
                        'type': 'string',
                        'format': 'email'
                    },
                    'to_email': {
                        'oneOf': [
                            {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                    'format': 'email'
                                }
                            },
                            {
                                'type': 'string',
                                'format': 'email'
                            }
                        ]
                    },
                    'inter_poll_sleep_sec': {'type': 'integer'},
                    'max_total_runtime_sec': {'type': 'integer'},
                    'email_subject': {'type': 'string'},
                    'failure_html_path': {'type': 'string'},
                    'failure_command': {'type': 'array'}
                }
            }
        }
    }

    def __init__(self):
        s = deepcopy(self.base_schema)
        jobclasses = get_job_classes()
        for clsname in sorted(jobclasses.keys()):
            s['definitions'][clsname] = schema_for_job_class(
                jobclasses[clsname]
            )
            s['properties']['jobs']['items']['anyOf'].append({
                '$ref': '#/definitions/%s' % clsname
            })
        self._schema = s

    @property
    def schema_dict(self):
        """
        Return the full generated schema dict.

        :return: generated JSONSchema
        :rtype: dict
        """
        return self._schema

    def validate(self, config_dict):
        """
        Validate the specified configuration dict against the schema.

        :param config_dict: configuration to validate
        :type config_dict: dict
        """
        jsonschema.validate(config_dict, self.schema_dict)
        jobnames = [j['name'] for j in config_dict['jobs']]
        dupes = [i for i, c in collections.Counter(jobnames).items() if c > 1]
        if len(dupes) > 0:
            raise RuntimeError(
                'ERROR: Duplicate Job names in configuration: %s' % dupes
            )
