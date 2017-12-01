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
from copy import copy
from time import sleep
from datetime import datetime, timedelta
from traceback import format_exc

from ecsjobs.version import VERSION, PROJECT_URL
from ecsjobs.config import Config
from ecsjobs.reporter import Reporter

logger = logging.getLogger(__name__)

# suppress requests logging
for lname in ['requests', 'botocore', 'boto3']:
    l = logging.getLogger(lname)
    l.setLevel(logging.WARNING)
    l.propagate = True


class EcsJobsRunner(object):

    def __init__(self, config, only_email_if_problems=False):
        self._conf = config
        self._finished = []
        self._running = []
        self._run_exceptions = {}
        self._start_time = None
        self._timeout = None
        self._only_email_if_problems = only_email_if_problems

    def run_schedules(self, schedule_names):
        """
        Run the named schedules.

        :param schedule_names: names of the schedules to run
        :type schedule_names: list
        """
        jobs = self._conf.jobs_for_schedules(schedule_names)
        logger.info('Running %d jobs for schedules %s: %s',
                    len(jobs), schedule_names, jobs)
        self._run_jobs(jobs)

    def run_job_names(self, job_names):
        """
        Run the named jobs, regardless of schedule.

        :param job_names: list of string job names to run
        :type job_names: list
        """
        jobs = [j for j in self._conf.jobs if j.name in job_names]
        logger.info('Running %d jobs for names %s: %s',
                    len(jobs), job_names, jobs)
        self._run_jobs(jobs, force_run=True)

    def _run_jobs(self, jobs, force_run=False):
        """
        Run the specified jobs.

        :param jobs: list of Job instances to run
        :type jobs: list
        :param force_run: Run each job regardless of cron expression
        :type force_run: bool
        """
        self._finished = []
        self._running = []
        self._run_exceptions = {}
        logger.info('Running %d jobs: %s', len(jobs), jobs)
        self._start_time = datetime.now()
        self._timeout = self._start_time + timedelta(
            seconds=self._conf.get_global('max_total_runtime_sec')
        )
        for j in jobs:
            logger.debug('now=%s timeout=%s', datetime.now(), self._timeout)
            if datetime.now() >= self._timeout:
                logger.error('Time limit reached; not running any more jobs!')
                self._running.append(j)
                continue
            if j.skip is not None and not force_run:
                logger.debug('Skipping job %s: %s', j.name, j.skip)
                self._finished.append(j)
                continue
            try:
                logger.debug('Running job: %s', j)
                res = j.run()
            except Exception as ex:
                logger.error('Job %s failed to run:\n%s', j, j.error_repr,
                             exc_info=True)
                self._run_exceptions[j] = (ex, format_exc())
                self._finished.append(j)
                continue
            if res is None:
                logger.info('Job %s still running; will poll for result', j)
                self._running.append(j)
            else:
                logger.info('Job %s finished (success=%s)', j, res)
                self._finished.append(j)
        self._poll_jobs()
        self._report()

    def _poll_jobs(self):
        """
        Poll the jobs in ``self._running``; if they're finished, move the Job
        to ``self._finished``.
        """
        sleep_sec = self._conf.get_global('inter_poll_sleep_sec')
        while len(self._running) > 0:
            if datetime.now() >= self._timeout:
                logger.error('Time limit reached; not polling any more jobs!')
                break
            logger.info('Polling %d running jobs...', len(self._running))
            for j in copy(self._running):
                if j.poll():
                    logger.info('Job %s finished', j)
                    self._running.remove(j)
                    self._finished.append(j)
                else:
                    logger.debug('Job %s still running', j)
            if len(self._running) > 0:
                logger.debug('Sleeping %ss before next poll', sleep_sec)
                sleep(sleep_sec)

    def _report(self):
        """Generate and send email report."""
        Reporter(self._conf).run(
            self._finished, self._running, self._run_exceptions,
            self._start_time, datetime.now(),
            only_email_if_problems=self._only_email_if_problems
        )


def parse_args(argv):
    actions = ['validate', 'run', 'list-schedules']
    p = argparse.ArgumentParser(description='ECS Jobs Wrapper/Runner')
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='ecsjobs v%s <%s>' % (VERSION, PROJECT_URL))
    p.add_argument('-m', '--only-email-if-problems', action='store_true',
                   dest='only_email_if_problems', default=False,
                   help='If specified, only send email report if at least one '
                        'job failed, raised an exception or was not run.')
    p.add_argument('ACTION', action='store', type=str, choices=actions,
                   help='Action to take; one of: %s' % actions)
    p.add_argument('-j', '--job', action='append', dest='jobs', default=[],
                   help='Job names to run, regardless of specified schedules '
                        'or cron expressions.')
    p.add_argument('SCHEDULES', action='store', nargs='*',
                   help='Schedule names to run; one or more.')
    args = p.parse_args(argv)
    if args.ACTION == 'run':
        if len(args.SCHEDULES) < 1 and len(args.jobs) < 1:
            raise RuntimeError(
                'ERROR: "run" action must have one or more SCHEDULES '
                'specified if jobs are not explicitly specified with -j / --job'
            )
        if len(args.SCHEDULES) > 0 and len(args.jobs) > 0:
            raise RuntimeError(
                'ERROR: SCHEDULES cannot be mixed with -j / --job.'
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
    if len(args.SCHEDULES) > 0:
        EcsJobsRunner(
            conf, only_email_if_problems=args.only_email_if_problems
        ).run_schedules(args.SCHEDULES)
    else:
        EcsJobsRunner(
            conf, only_email_if_problems=args.only_email_if_problems
        ).run_job_names(args.jobs)


if __name__ == "__main__":
    main(argv=sys.argv[1:])
