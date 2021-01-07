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

from unittest.mock import patch, call, Mock, DEFAULT, mock_open
from freezegun import freeze_time

import pytest
import yaml

from ecsjobs.config import Config

pbm = 'ecsjobs.config'
pb = '%s.Config' % pbm


class ConfigTester(object):

    def setup(self):
        with patch('%s.logger' % pbm, autospec=True) as self.mock_logger:
            with patch(
                '%s.boto3.resource' % pbm, autospec=True
            ) as self.mock_s3:
                with patch.multiple(
                    '%s.Config' % pbm,
                    autospec=True,
                    _load_config=DEFAULT,
                    _validate_config=DEFAULT,
                    _make_jobs=DEFAULT
                ):
                    self.cls = Config()
        self.mock_s3.reset_mock()


class TestInit(object):

    def test_init(self):
        m_s3 = Mock()
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.boto3.resource' % pbm, autospec=True
            ) as mock_s3:
                mock_s3.return_value = m_s3
                with patch.multiple(
                    '%s.Config' % pbm,
                    autospec=True,
                    _load_config=DEFAULT,
                    _validate_config=DEFAULT,
                    _make_jobs=DEFAULT
                ) as mocks:
                    cls = Config()
        assert cls.s3 == m_s3
        assert cls._global_conf == {}
        assert cls._jobs == []
        assert cls._raw_conf == {}
        assert mock_logger.mock_calls == []
        assert mock_s3.mock_calls == [
            call('s3')
        ]
        assert mocks['_load_config'].mock_calls == [call(cls)]
        assert mocks['_validate_config'].mock_calls == [call(cls)]
        assert mocks['_make_jobs'].mock_calls == [call(cls)]


class TestJobs(ConfigTester):

    def test_jobs(self):
        self.cls._jobs = [1, 2, 3]
        assert self.cls.jobs == [1, 2, 3]


class TestKeyIsYaml(ConfigTester):

    def test_yml(self):
        assert self.cls._key_is_yaml('foo/bar/baz.yml') is True

    def test_yaml(self):
        assert self.cls._key_is_yaml('foo/bar/baz.yaml') is True

    def test_txt(self):
        assert self.cls._key_is_yaml('foo/bar/baz.txt') is False


class TestLoadConfig(ConfigTester):

    def test_s3(self):
        with patch.dict(
            '%s.os.environ' % pbm,
            {
                'ECSJOBS_BUCKET': 'bname',
                'ECSJOBS_KEY': 'kname'
            },
            clear=True
        ):
            with patch.multiple(
                pb,
                autospec=True,
                _load_config_s3=DEFAULT,
                _load_config_local=DEFAULT
            ) as mocks:
                self.cls._load_config()
        assert mocks['_load_config_s3'].mock_calls == [
            call(self.cls, 'bname', 'kname')
        ]
        assert mocks['_load_config_local'].mock_calls == []

    def test_local(self):
        with patch.dict(
            '%s.os.environ' % pbm,
            {
                'ECSJOBS_LOCAL_CONF_PATH': '/conf/path'
            },
            clear=True
        ):
            with patch.multiple(
                pb,
                autospec=True,
                _load_config_s3=DEFAULT,
                _load_config_local=DEFAULT
            ) as mocks:
                self.cls._load_config()
        assert mocks['_load_config_s3'].mock_calls == []
        assert mocks['_load_config_local'].mock_calls == [
            call(self.cls, '/conf/path')
        ]

    def test_failure(self):
        with patch.dict('%s.os.environ' % pbm, {}, clear=True):
            with patch.multiple(
                pb,
                autospec=True,
                _load_config_s3=DEFAULT,
                _load_config_local=DEFAULT
            ) as mocks:
                with pytest.raises(RuntimeError) as exc:
                    self.cls._load_config()
        assert str(exc.value) == 'ERROR: You must export either ' \
                                 'ECSJOBS_BUCKET and ECSJOBS_KEY, ' \
                                 'or ECSJOBS_LOCAL_CONF_PATH'
        assert mocks['_load_config_s3'].mock_calls == []
        assert mocks['_load_config_local'].mock_calls == []


class TestLoadYamlFromDisk(ConfigTester):

    def test_load_from_disk(self):
        content = "foo: bar\nbaz: blam\n"
        with patch(
            '%s.open' % pbm, mock_open(read_data=content), create=True
        ) as m:
            res = self.cls._load_yaml_from_disk('/foo/bar.yml')
        assert res == {'foo': 'bar', 'baz': 'blam'}
        assert m.mock_calls == [
            call('/foo/bar.yml', 'r'),
            call().__enter__(),
            call().read(4096),
            call().read(4096),
            call().__exit__(None, None, None)
        ]


class TestLoadConfigS3(ConfigTester):

    def test_single_file(self):
        self.cls._key_name = 'foo/bar/config.yml'
        assert self.cls._raw_conf == {}
        with patch.multiple(
            pb,
            autospec=True,
            _get_yaml_from_s3=DEFAULT,
            _key_is_yaml=DEFAULT,
            _get_multipart_config=DEFAULT
        ) as mocks:
            mocks['_get_yaml_from_s3'].return_value = {'my': 'config'}
            mocks['_key_is_yaml'].return_value = True
            self.cls._load_config_s3('bname', 'foo/bar/config.yml')
        assert self.cls._raw_conf == {'my': 'config'}
        assert self.mock_s3.mock_calls == [
            call().Bucket('bname')
        ]
        assert mocks['_get_yaml_from_s3'].mock_calls == [
            call(
                self.cls,
                self.mock_s3.return_value.Bucket.return_value,
                'foo/bar/config.yml'
            )
        ]
        assert mocks['_key_is_yaml'].mock_calls == [
            call(self.cls, 'foo/bar/config.yml')
        ]
        assert mocks['_get_multipart_config'].mock_calls == []

    def test_multi_file(self):
        self.cls._key_name = 'foo/bar/config'
        assert self.cls._raw_conf == {}
        with patch.multiple(
            pb,
            autospec=True,
            _get_yaml_from_s3=DEFAULT,
            _key_is_yaml=DEFAULT,
            _get_multipart_config=DEFAULT
        ) as mocks:
            mocks['_get_multipart_config'].return_value = {'my': 'config'}
            mocks['_key_is_yaml'].return_value = False
            self.cls._load_config_s3('bname', 'foo/bar/config')
        assert self.cls._raw_conf == {'my': 'config'}
        assert self.mock_s3.mock_calls == [
            call().Bucket('bname')
        ]
        assert mocks['_get_yaml_from_s3'].mock_calls == []
        assert mocks['_get_multipart_config'].mock_calls == [
            call(
                self.cls,
                self.mock_s3.return_value.Bucket.return_value,
                'foo/bar/config'
            )
        ]
        assert mocks['_key_is_yaml'].mock_calls == [
            call(self.cls, 'foo/bar/config')
        ]


class TestLoadConfigLocal(ConfigTester):

    def test_multi_file(self):

        def se_lyfd(klass, path):
            return {'path': path}

        assert self.cls._raw_conf == {}
        with patch('%s._load_yaml_from_disk' % pb, autospec=True) as m_lyfd:
            m_lyfd.side_effect = se_lyfd
            with patch('%s.glob.glob' % pbm) as mock_glob:
                mock_glob.side_effect = [
                    ['/conf/path/foo.yml', '/conf/path/global.yml'],
                    ['/conf/path/bar.yaml', '/conf/path/zzz.yaml']
                ]
                with patch('%s.os.path.exists' % pbm) as mock_ope:
                    mock_ope.return_value = True
                    with patch('%s.os.path.isdir' % pbm) as mock_opid:
                        mock_opid.return_value = True
                        self.cls._load_config_local('/conf/path')
        assert self.cls._raw_conf == {
            'global': {'path': '/conf/path/global.yml'},
            'jobs': [
                {'path': '/conf/path/bar.yaml'},
                {'path': '/conf/path/foo.yml'},
                {'path': '/conf/path/zzz.yaml'}
            ]
        }
        assert mock_ope.mock_calls == [call('/conf/path')]
        assert mock_opid.mock_calls == [call('/conf/path')]
        assert mock_glob.mock_calls == [
            call('/conf/path/*.yml'),
            call('/conf/path/*.yaml'),
        ]
        assert m_lyfd.mock_calls == [
            call(self.cls, '/conf/path/bar.yaml'),
            call(self.cls, '/conf/path/foo.yml'),
            call(self.cls, '/conf/path/global.yml'),
            call(self.cls, '/conf/path/zzz.yaml')
        ]

    def test_multi_file_trailing_slash(self):

        def se_lyfd(klass, path):
            return {'path': path}

        assert self.cls._raw_conf == {}
        with patch('%s._load_yaml_from_disk' % pb, autospec=True) as m_lyfd:
            m_lyfd.side_effect = se_lyfd
            with patch('%s.glob.glob' % pbm) as mock_glob:
                mock_glob.side_effect = [
                    ['/conf/path/foo.yml', '/conf/path/global.yml'],
                    ['/conf/path/bar.yaml', '/conf/path/zzz.yaml']
                ]
                with patch('%s.os.path.exists' % pbm) as mock_ope:
                    mock_ope.return_value = True
                    with patch('%s.os.path.isdir' % pbm) as mock_opid:
                        mock_opid.return_value = True
                        self.cls._load_config_local('/conf/path/')
        assert self.cls._raw_conf == {
            'global': {'path': '/conf/path/global.yml'},
            'jobs': [
                {'path': '/conf/path/bar.yaml'},
                {'path': '/conf/path/foo.yml'},
                {'path': '/conf/path/zzz.yaml'}
            ]
        }
        assert mock_ope.mock_calls == [call('/conf/path/')]
        assert mock_opid.mock_calls == [call('/conf/path/')]
        assert mock_glob.mock_calls == [
            call('/conf/path/*.yml'),
            call('/conf/path/*.yaml'),
        ]
        assert m_lyfd.mock_calls == [
            call(self.cls, '/conf/path/bar.yaml'),
            call(self.cls, '/conf/path/foo.yml'),
            call(self.cls, '/conf/path/global.yml'),
            call(self.cls, '/conf/path/zzz.yaml')
        ]

    def test_single_file(self):

        def se_lyfd(klass, path):
            return {'path': path}

        assert self.cls._raw_conf == {}
        with patch('%s._load_yaml_from_disk' % pb, autospec=True) as m_lyfd:
            m_lyfd.side_effect = se_lyfd
            with patch('%s.glob.glob' % pbm) as mock_glob:
                with patch('%s.os.path.exists' % pbm) as mock_ope:
                    mock_ope.return_value = True
                    with patch('%s.os.path.isdir' % pbm) as mock_opid:
                        mock_opid.return_value = False
                        self.cls._load_config_local('/conf/path')
        assert self.cls._raw_conf == {
            'path': '/conf/path'
        }
        assert mock_ope.mock_calls == [call('/conf/path')]
        assert mock_opid.mock_calls == [call('/conf/path')]
        assert mock_glob.mock_calls == []
        assert m_lyfd.mock_calls == [
            call(self.cls, '/conf/path')
        ]

    def test_path_does_not_exist(self):

        def se_lyfd(klass, path):
            return {'path': path}

        assert self.cls._raw_conf == {}
        with patch('%s._load_yaml_from_disk' % pb, autospec=True) as m_lyfd:
            m_lyfd.side_effect = se_lyfd
            with patch('%s.glob.glob' % pbm) as mock_glob:
                with patch('%s.os.path.exists' % pbm) as mock_ope:
                    mock_ope.return_value = False
                    with patch('%s.os.path.isdir' % pbm) as mock_opid:
                        mock_opid.return_value = False
                        with pytest.raises(RuntimeError) as exc:
                            self.cls._load_config_local('/conf/path')
        assert str(exc.value) == 'ERROR: Config path does not exist: /conf/path'
        assert mock_ope.mock_calls == [call('/conf/path')]
        assert mock_opid.mock_calls == []
        assert mock_glob.mock_calls == []
        assert m_lyfd.mock_calls == []


class TestGetMultipartConfig(ConfigTester):

    def test_simple(self):

        def se_key_is_yaml(klass, k):
            if k.endswith('.yml'):
                return True
            if k.endswith('.yaml'):
                return True
            return False

        m_obj1 = Mock(key='/foo/bar/conf/job1.yml')
        m_obj2 = Mock(key='/foo/bar/conf/foo.txt')
        m_obj3 = Mock(key='/foo/bar/conf/global.yaml')
        m_obj4 = Mock(key='/foo/bar/conf/global.pdf')
        m_obj5 = Mock(key='/foo/bar/conf/job2.yaml')
        bkt = Mock()
        bkt.objects.filter.return_value = [
            m_obj1, m_obj2, m_obj3, m_obj4, m_obj5
        ]
        with patch.multiple(
            pb,
            autospec=True,
            _key_is_yaml=DEFAULT,
            _get_yaml_from_s3=DEFAULT
        ) as mocks:
            mocks['_key_is_yaml'].side_effect = se_key_is_yaml
            mocks['_get_yaml_from_s3'].side_effect = [
                {'conf': 'global'},
                {'conf': 'job1'},
                {'conf': 'job2'}
            ]
            res = self.cls._get_multipart_config(bkt, '/foo/bar/conf/')
        assert res == {
            'global': {'conf': 'global'},
            'jobs': [
                {'conf': 'job1'},
                {'conf': 'job2'}
            ]
        }
        assert bkt.mock_calls == [
            call.objects.filter(Prefix='/foo/bar/conf/')
        ]
        assert mocks['_key_is_yaml'].mock_calls == [
            call(self.cls, 'foo.txt'),
            call(self.cls, 'global.pdf'),
            call(self.cls, 'global.yaml'),
            call(self.cls, 'job1.yml'),
            call(self.cls, 'job2.yaml')
        ]
        assert mocks['_get_yaml_from_s3'].mock_calls == [
            call(self.cls, bkt, '/foo/bar/conf/global.yaml'),
            call(self.cls, bkt, '/foo/bar/conf/job1.yml'),
            call(self.cls, bkt, '/foo/bar/conf/job2.yaml')
        ]


class TestGetYamlFromS3(ConfigTester):

    def test_success(self):
        content = "foo: bar\nbaz: 123\n"
        expected = {'foo': 'bar', 'baz': 123}
        m_body = Mock()
        m_body.read.return_value = content
        m_obj = Mock(key='foo/bar/baz.yml')
        m_obj.get.return_value = {'Body': m_body}
        m_bkt = Mock()
        m_bkt.Object.return_value = m_obj
        with patch('%s.yaml.load' % pbm) as m_load:
            m_load.return_value = expected
            res = self.cls._get_yaml_from_s3(m_bkt, 'foo/bar/baz.yml')
        assert res == expected
        assert m_bkt.mock_calls == [
            call.Object('foo/bar/baz.yml'),
            call.Object().get()
        ]
        assert m_obj.mock_calls == [call.get()]
        assert m_body.mock_calls == [call.read()]
        assert m_load.mock_calls == [call(content, Loader=yaml.FullLoader)]

    def test_no_object(self):
        content = "foo: bar\nbaz: 123\n"
        expected = {'foo': 'bar', 'baz': 123}
        m_body = Mock()
        m_body.read.return_value = content
        m_obj = Mock(key='foo/bar/baz.yml')
        m_obj.get.return_value = {'Body': m_body}
        m_bkt = Mock(name='bname')
        m_bkt.Object.side_effect = NotImplementedError('foo')
        with patch('%s.yaml.load' % pbm) as m_load:
            m_load.return_value = expected
            with pytest.raises(RuntimeError) as exc:
                self.cls._get_yaml_from_s3(m_bkt, 'foo/bar/baz.yml')
                assert str(exc.value) == 'ERROR: Unable to retrieve key ' \
                                         'foo/bar/baz.yml from bucket bname'
        assert m_bkt.mock_calls == [
            call.Object('foo/bar/baz.yml')
        ]
        assert m_obj.mock_calls == []
        assert m_body.mock_calls == []
        assert m_load.mock_calls == []

    def test_cant_get(self):
        content = "foo: bar\nbaz: 123\n"
        expected = {'foo': 'bar', 'baz': 123}
        m_body = Mock()
        m_body.read.return_value = content
        m_obj = Mock(key='foo/bar/baz.yml')
        m_obj.get.side_effect = NotImplementedError('foo')
        m_bkt = Mock(name='bname')
        m_bkt.Object.return_value = m_obj
        with patch('%s.yaml.load' % pbm) as m_load:
            m_load.return_value = expected
            with pytest.raises(RuntimeError) as exc:
                self.cls._get_yaml_from_s3(m_bkt, 'foo/bar/baz.yml')
                assert str(exc.value) == 'ERROR: Unable to read key ' \
                                         'foo/bar/baz.yml from bucket bname'
        assert m_bkt.mock_calls == [
            call.Object('foo/bar/baz.yml'),
            call.Object().get()
        ]
        assert m_obj.mock_calls == [call.get()]
        assert m_body.mock_calls == []
        assert m_load.mock_calls == []

    def test_cant_load_yaml(self):
        content = "foo: bar\nbaz: 123\n"
        m_body = Mock()
        m_body.read.return_value = content
        m_obj = Mock(key='foo/bar/baz.yml')
        m_obj.get.return_value = {'Body': m_body}
        m_bkt = Mock(name='bname')
        m_bkt.Object.return_value = m_obj
        with patch('%s.yaml.load' % pbm) as m_load:
            m_load.side_effect = NotImplementedError('foo')
            with pytest.raises(RuntimeError) as exc:
                self.cls._get_yaml_from_s3(m_bkt, 'foo/bar/baz.yml')
                assert str(exc.value) == 'ERROR: Unable to load YAML from ' \
                                         'key foo/bar/baz.yml from bucket bname'
        assert m_bkt.mock_calls == [
            call.Object('foo/bar/baz.yml'),
            call.Object().get()
        ]
        assert m_obj.mock_calls == [call.get()]
        assert m_body.mock_calls == [call.read()]
        assert m_load.mock_calls == [call(content, Loader=yaml.FullLoader)]


class TestScheduleNames(ConfigTester):

    def test_schedule_names(self):
        self.cls._jobs = [
            Mock(schedule_name='foo'),
            Mock(schedule_name='bar'),
            Mock(schedule_name='foo'),
            Mock(schedule_name='blam'),
        ]
        assert self.cls.schedule_names == ['bar', 'blam', 'foo']


class TestJobsForSchedule(ConfigTester):

    def test_jobs_for_schedules(self):
        j1 = FakeJob(schedule_name='foo')
        j2 = FakeJob(schedule_name='bar')
        j3 = FakeJob(schedule_name='baz')
        j4 = FakeJob(schedule_name='blam')
        j5 = FakeJob(schedule_name='bar')
        self.cls._jobs = [j1, j2, j3, j4, j5]
        assert self.cls.jobs_for_schedules(['bar', 'quux']) == [j2, j5]


class FakeJob(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        if 'schedule_name' in kwargs:
            self.schedule_name = kwargs['schedule_name']


class TestValidate(ConfigTester):

    def test_validate(self):
        self.cls._raw_conf = {
            'global': {'foo': 'bar'},
            'jobs': ['one', 'two']
        }
        assert self.cls._global_conf == {}
        with patch('%s.Schema' % pbm, autospec=True) as m_schema:
            self.cls._validate_config()
        assert self.cls._global_conf == self.cls._raw_conf['global']
        assert m_schema.mock_calls == [
            call(),
            call().validate(self.cls._raw_conf)
        ]

    @freeze_time('2017-11-23 12:34:56')
    def test_validate_failure_html_path_date(self):
        self.cls._raw_conf = {
            'global': {
                'foo': 'bar',
                'failure_html_path': '/foo/bar/{date}.html'
            },
            'jobs': ['one', 'two']
        }
        assert self.cls._global_conf == {}
        with patch('%s.Schema' % pbm, autospec=True) as m_schema:
            self.cls._validate_config()
        assert self.cls._global_conf == {
            'foo': 'bar',
            'failure_html_path': '/foo/bar/2017-11-23T12-34-56.html'
        }
        assert m_schema.mock_calls == [
            call(),
            call().validate(self.cls._raw_conf)
        ]


class TestMakeJobs(ConfigTester):

    def test_success(self):
        jclasses = {
            'Foo': FakeJob,
            'Bar': FakeJob
        }
        self.cls._raw_conf['jobs'] = [
            {'class_name': 'Foo', 'name': 'foo', 'schedule': 's1', 'bar': 'b'},
            {'class_name': 'Foo', 'name': 'foo2', 'schedule': 's2'},
            {'class_name': 'Bar', 'name': 'bar', 'schedule': 's1'},
        ]
        with patch('%s.get_job_classes' % pbm) as mock_gjc:
            mock_gjc.return_value = jclasses
            self.cls._make_jobs()
        assert len(self.cls._jobs) == 3
        assert self.cls._jobs[0].kwargs == {
            'name': 'foo', 'schedule': 's1', 'bar': 'b'
        }
        assert self.cls._jobs[1].kwargs == {
            'name': 'foo2', 'schedule': 's2'
        }
        assert self.cls._jobs[2].kwargs == {
            'name': 'bar', 'schedule': 's1'
        }

    def test_error(self):
        jclasses = {
            'Foo': FakeJob
        }
        self.cls._raw_conf['jobs'] = [
            {'class_name': 'Foo', 'name': 'foo', 'schedule': 's1'},
            {'class_name': 'Foo', 'name': 'foo2', 'schedule': 's2'},
            {'class_name': 'Bar', 'name': 'bar', 'schedule': 's1'},
        ]
        with patch('%s.get_job_classes' % pbm) as mock_gjc:
            mock_gjc.return_value = jclasses
            with pytest.raises(RuntimeError) as exc:
                self.cls._make_jobs()
        assert str(exc.value) == 'ERROR: No known Job subclass "Bar" (job bar)'
        assert len(self.cls._jobs) == 2
        assert self.cls._jobs[0].kwargs == {
            'name': 'foo', 'schedule': 's1'
        }
        assert self.cls._jobs[1].kwargs == {
            'name': 'foo2', 'schedule': 's2'
        }


class TestGetGlobal(ConfigTester):

    def test_get_in_conf(self):
        self.cls._global_conf = {'foo': 'bar'}
        assert self.cls._global_conf.get('foo') == 'bar'
        assert self.cls.get_global('foo') == 'bar'

    def test_get_defaults(self):
        assert self.cls.get_global('inter_poll_sleep_sec') == 10
