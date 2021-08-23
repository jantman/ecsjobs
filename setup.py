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

from setuptools import setup, find_packages
from ecsjobs.version import VERSION, PROJECT_URL

with open('README.rst') as file:
    long_description = file.read()

requires = [
    'boto3>=1.0.0,<2.0.0',
    'cronex==0.1.0',
    'docker>=2.0.0,<3.0.0',
    'jsonschema>=2.0.0,<3.0.0',
    'PyYAML>=3.0',
    'requests>=2.0.0,<3.0.0'
]

classifiers = [
    'Development Status :: 6 - Mature',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: GNU Affero General Public License '
    'v3 or later (AGPLv3+)',
]

setup(
    name='ecsjobs',
    version=VERSION,
    author='Jason Antman',
    author_email='jason@jasonantman.com',
    packages=find_packages(),
    url=PROJECT_URL,
    description='A scheduled job wrapper for ECS, focused on email reporting '
                'and adding docker exec and local command abilities.',
    long_description=long_description,
    install_requires=requires,
    keywords="aws ecs cron email docker",
    classifiers=classifiers,
    entry_points="""
    [console_scripts]
    ecsjobs = ecsjobs.runner:main
    """,
)
