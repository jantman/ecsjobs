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

import sys
import argparse
import logging

from ecsjobs.version import VERSION, PROJECT_URL
from ecsjobs.config import Config

logger = logging.getLogger(__name__)

# suppress requests logging
for lname in ['requests', 'botocore', 'boto3']:
    l = logging.getLogger(lname)
    l.setLevel(logging.WARNING)
    l.propagate = True


class EcsJobsRunner(object):

    def __init__(self, config):
        self._conf = config

    def run_schedules(self, schedule_names):
        """
        Run the named schedules.

        :param schedule_names: names of the schedules to run
        :type schedule_names: list
        """
        raise NotImplementedError()


def parse_args(argv):
    actions = ['validate', 'run', 'list-schedules']
    p = argparse.ArgumentParser(description='ECS Jobs Wrapper/Runner')
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='ecsjobs v%s <%s>' % (VERSION, PROJECT_URL))
    p.add_argument('ACTION', action='store', type=str, choices=actions,
                   help='Action to take; one of: %s' % actions)
    p.add_argument('SCHEDULES', action='store', nargs='*',
                   help='Schedule names to run; one or more.')
    args = p.parse_args(argv)
    if args.ACTION == 'run' and len(args.SCHEDULES) < 1:
        raise RuntimeError(
            'ERROR: "run" action must have one or more SCHEDULES specified'
        )
    return args


def set_log_info(logger):
    """
    set logger level to INFO via :py:func:`~.set_log_level_format`.
    """
    set_log_level_format(logger, logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug(logger):
    """
    set logger level to DEBUG, and debug-level output format,
    via :py:func:`~.set_log_level_format`.
    """
    set_log_level_format(
        logger,
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(logger, level, format):
    """
    Set logger level and format.

    :param logger: the logger object to set on
    :type logger: logging.Logger
    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    global logger
    format = "[%(asctime)s %(levelname)s] %(message)s"
    logging.basicConfig(level=logging.WARNING, format=format)
    logger = logging.getLogger()

    args = parse_args(argv)

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    conf = Config()
    if args.ACTION == 'validate':
        # this was done when loading the config
        raise SystemExit(0)
    if args.ACTION == 'list-schedules':
        for s in conf.schedule_names:
            print(s)
        raise SystemExit(0)
    EcsJobsRunner(conf).run_schedules(args.SCHEDULES)


if __name__ == "__main__":
    main(argv=sys.argv[1:])
