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

from unittest.mock import patch, call, Mock, DEFAULT, PropertyMock, MagicMock  # noqa

import pytest

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
                    self.cls = Config('bname', 'kname')
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
                    cls = Config('bname', 'kname')
        assert cls._bucket_name == 'bname'
        assert cls._key_name == 'kname'
        assert cls.s3 == m_s3
        assert cls._global_conf == {}
        assert cls._jobs_conf == []
        assert cls._jobs == {}
        assert cls._raw_conf == {}
        assert mock_logger.mock_calls == [
            call.debug('Initializing Config using bucket_name=%s key_name=%s',
                       'bname', 'kname')
        ]
        assert mock_s3.mock_calls == [
            call('s3')
        ]
        assert mocks['_load_config'].mock_calls == [call(cls)]
        assert mocks['_validate_config'].mock_calls == [call(cls)]
        assert mocks['_make_jobs'].mock_calls == [call(cls)]


class TestKeyIsYaml(ConfigTester):

    def test_yml(self):
        assert self.cls._key_is_yaml('foo/bar/baz.yml') is True

    def test_yaml(self):
        assert self.cls._key_is_yaml('foo/bar/baz.yaml') is True

    def test_txt(self):
        assert self.cls._key_is_yaml('foo/bar/baz.txt') is False


class TestLoadConfig(ConfigTester):

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
            self.cls._load_config()
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
            self.cls._load_config()
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


class TestGetMultipartConfig(ConfigTester):

    def test_simple(self):
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
            mocks['_key_is_yaml'].side_effect = [True, False, True, False, True]
            mocks['_get_yaml_from_s3'].side_effect = [
                {'conf': 'job1'},
                {'conf': 'global'},
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
            call(self.cls, 'job1.yml'),
            call(self.cls, 'foo.txt'),
            call(self.cls, 'global.yaml'),
            call(self.cls, 'global.pdf'),
            call(self.cls, 'job2.yaml')
        ]
        assert mocks['_get_yaml_from_s3'].mock_calls == [
            call(self.cls, bkt, '/foo/bar/conf/job1.yml'),
            call(self.cls, bkt, '/foo/bar/conf/global.yaml'),
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
        assert m_load.mock_calls == [call(content)]

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
        assert m_load.mock_calls == [call(content)]


class TestScheduleNames(ConfigTester):

    def test_schedule_names(self):
        self.cls._jobs = {
            'foo': Mock(schedule_name='foo'),
            'bar': Mock(schedule_name='bar'),
            'baz': Mock(schedule_name='foo'),
            'blam': Mock(schedule_name='blam'),
        }
        assert self.cls.schedule_names == ['bar', 'blam', 'foo']


class FakeJob(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class TestMakeJobs(ConfigTester):

    def test_success(self):
        jclasses = {
            'Foo': FakeJob,
            'Bar': FakeJob
        }
        self.cls._raw_conf['jobs'] = [
            {'class_name': 'Foo', 'name': 'foo', 'schedule': 's1'},
            {'class_name': 'Foo', 'name': 'foo2', 'schedule': 's2'},
            {'class_name': 'Bar', 'name': 'bar', 'schedule': 's1'},
        ]
        with patch('%s.jobclasses' % pbm, jclasses):
            self.cls._make_jobs()
        assert len(self.cls._jobs) == 3
        assert self.cls._jobs['foo'].kwargs == {
            'class_name': 'Foo', 'name': 'foo', 'schedule': 's1'
        }
        assert self.cls._jobs['foo2'].kwargs == {
            'class_name': 'Foo', 'name': 'foo2', 'schedule': 's2'
        }
        assert self.cls._jobs['bar'].kwargs == {
            'class_name': 'Bar', 'name': 'bar', 'schedule': 's1'
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
        with patch('%s.jobclasses' % pbm, jclasses):
            with pytest.raises(RuntimeError) as exc:
                self.cls._make_jobs()
        assert str(exc.value) == 'ERROR: No known Job subclass "Bar" (job bar)'
        assert len(self.cls._jobs) == 2
        assert self.cls._jobs['foo'].kwargs == {
            'class_name': 'Foo', 'name': 'foo', 'schedule': 's1'
        }
        assert self.cls._jobs['foo2'].kwargs == {
            'class_name': 'Foo', 'name': 'foo2', 'schedule': 's2'
        }
