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

from os import close as os_close
import logging
from getpass import getuser
from socket import gethostname
from datetime import datetime
from html import escape
from tempfile import mkstemp
from subprocess import Popen, PIPE, STDOUT

import boto3

logger = logging.getLogger(__name__)


class Reporter(object):
    """ECSJobs Report Generator and SES Sender"""

    def __init__(self, config):
        """
        Initialize the Report generator.

        :param config: Configuration
        :type config: ecsjobs.config.Config
        """
        self._config = config
        self._ses = boto3.client('ses')
        self._have_failures = False

    def run(self, finished, unfinished, excs, start_dt, end_dt,
            only_email_if_problems=False):
        """
        Generate and send the report.

        :param finished: Finished Job instances.
        :type finished: list
        :param unfinished: Unfinished (timed-out) Job instances.
        :type unfinished: list
        :param excs: Dict of Jobs that generated an exception while running;
          keys are Job class instances and values are 2-tuples of the caught
          Exception objects and string formatted tracebacks.
        :type excs: dict
        :param start_dt: datetime instance when run was started
        :type start_dt: datetime.datetime
        :param end_dt: datetime instance when run was finished
        :type end_dt: datetime.datetime
        :param only_email_if_problems: If True, only send email report if there
          were failures, exceptions, or unfinished jobs. Otherwise, always send
          email.
        :type only_email_if_problems: bool
        """
        self._have_failures = False
        report = self._make_report(finished, unfinished, excs, start_dt, end_dt)
        if only_email_if_problems and not self._have_failures:
            logger.info('only_email_if_problems is True and no problems; '
                        'not sending email')
            return
        to_addr = self._config.get_global('to_email')
        if not isinstance(to_addr, type([])):
            to_addr = [to_addr]
        try:
            resp = self._ses.send_email(
                Source=self._config.get_global('from_email'),
                Destination={
                    'ToAddresses': to_addr
                },
                Message={
                    'Subject': {
                        'Data': self._config.get_global('email_subject'),
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': report,
                            'Charset': 'utf-8'
                        }
                    }
                },
                ReturnPath=self._config.get_global('from_email'),
            )
            logger.info('Sent email via SES: %s', resp)
        except Exception:
            logger.error('ERROR sending email to %s via SES. Email Body:\n%s',
                         self._config.get_global('to_email'), report,
                         exc_info=True)
            failure_cmd = self._config.get_global('failure_command')
            if failure_cmd is not None:
                try:
                    p = Popen(
                        *failure_cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                        universal_newlines=True
                    )
                    out = p.communicate(input='\n\n%s' % report, timeout=120)[0]
                    logger.warning(
                        'Failure command (%s) exited %s with output:\n%s',
                        failure_cmd, p.returncode, out
                    )
                except Exception:
                    logger.error(
                        'Exception while running failure_cmd %s', failure_cmd,
                        exc_info=True
                    )
            failure_path = self._config.get_global('failure_html_path')
            if failure_path is None:
                fd, path = mkstemp(prefix='ecsjobs', text=True, suffix='.html')
                with open(path, 'w') as fh:
                    fh.write(report)
                os_close(fd)
                logger.warning('HTML report written to: %s', path)
            else:
                with open(failure_path, 'w') as fh:
                    fh.write(report)
                logger.warning('HTML report written to: %s', failure_path)
            raise

    def _make_report(self, finished, unfinished, excs, start_dt, end_dt):
        """
        Generate the HTML email report

        :param finished: Finished Job instances.
        :type finished: list
        :param unfinished: Unfinished (timed-out) Job instances.
        :type unfinished: list
        :param excs: Dict of Jobs that generated an exception while running;
          keys are Job class instances and values are 2-tuples of the caught
          Exception objects and string formatted tracebacks.
        :type excs: dict
        :param start_dt: datetime instance when run was started
        :type start_dt: datetime.datetime
        :param end_dt: datetime instance when run was finished
        :type end_dt: datetime.datetime
        :returns: HTML email report content
        :rtype: str
        """
        html = "<p>ECSJobs run report for %s@%s at %s</p>\n" % (
            getuser(), gethostname(),
            datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S %Z')
        )
        html += '<p>Total Duration: %s</p>\n' % str(end_dt - start_dt)
        html += '<table style="border: 1px solid black; ' \
                'border-collapse: collapse;">' + "\n"
        html += '<tr>'
        html += self.th('Job Name')
        html += self.th('Exit Code')
        html += self.th('Duration')
        html += self.th('Message')
        html += '</tr>' + "\n"
        for j in finished:
            html += self._tr_for_job(j, exc=excs.get(j, None))
        for j in unfinished:
            html += self._tr_for_job(j, unfinished=True)
        html += '</table>' + "\n"
        for j in finished:
            html += self._div_for_job(j, exc=excs.get(j, None))
            html += '<hr />' + "\n"
        for j in unfinished:
            html += self._div_for_job(j, unfinished=True)
            html += '<hr />' + "\n"
        return html

    def th(self, s):
        return '<th style="border: 1px solid black;">%s</th>' % s

    def td(self, s):
        return '<td style="border: 1px solid black; padding: 1em;">%s</td>' % s

    def _tr_for_job(self, job, exc=None, unfinished=False):
        """
        Generate a row in the results table for a specific job.

        :param job: the Job to generate a div for
        :type job: ecsjobs.jobs.base.Job
        :param exc: None or 2-tuple of Exception caught when running job and
          traceback formatted as a string.
        :type exc: ``2-tuple`` or ``None``
        :param unfinished: whether or not the job was killed before being
          finished.
        :type unfinished: bool
        :return: Table row for the report
        :rtype: str
        """
        bg = '#66ff66'
        if exc is not None:
            bg = '#ff9999'
        elif job.skip is not None:
            bg = '#fffc4d'
        elif unfinished:
            bg = '#ff944d'
            self._have_failures = True
        elif job.exitcode != 0:
            bg = '#ff9999'
            self._have_failures = True
        res = '<tr style="background-color: %s;">' % bg
        res += self.td('<a href="#%s">%s</a>' % (job.name, job.name))
        if unfinished:
            res += self.td('Unfinished')
            res += self.td(job.duration)
            res += self.td('<em>Unfinished</em>')
        elif exc is not None:
            res += self.td('Exception')
            res += self.td(job.duration)
            res += self.td(
                escape('%s: %s' % (exc[0].__class__.__name__, exc[0]))
            )
            self._have_failures = True
        elif job.skip is not None:
            res += self.td('Skipped')
            res += self.td('&nbsp;')
            res += self.td(escape(job.skip))
        else:
            res += self.td(job.exitcode)
            res += self.td(job.duration)
            res += self.td(escape(job.summary()))
        res += '</tr>' + "\n"
        return res

    def _div_for_job(self, job, exc=None, unfinished=False):
        """
        Generate a div for the results email with the output or exception of a
        specific job.

        :param job: the Job to generate a div for
        :type job: ecsjobs.jobs.base.Job
        :param exc: Exception caught when running job, or None
        :type exc: ``Exception`` or ``None``
        :param unfinished: whether or not the job was killed before being
          finished.
        :type unfinished: bool
        :return: HTML div for the report
        :rtype: str
        """
        res = '<div><p><strong><a name="%s">%s</a></strong> - %s</p>' % (
            job.name, job.name, escape(str(job.report_description()))
        )
        if exc is not None:
            res += '<pre>%s\n\n%s</pre>' % (
                escape(job.error_repr), escape(exc[1])
            )
        elif unfinished:
            res += '<pre>%s</pre>\n<strong>JOB NOT FINISHED.</strong>' \
                   '' % escape(job.error_repr)
        elif job.skip is not None:
            res += '<p>Job Skipped: %s</p>' % escape(job.skip)
        else:
            res += '<pre>%s</pre>' % escape(job.output)
        res += '</div>' + "\n"
        return res
