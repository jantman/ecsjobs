import testinfra
import pytest
import os
from ecsbuild.test_helpers import *


class TestInternal(object):

    def setup(self):
        self.host = testinfra.get_host(
            "docker://" + os.environ['PYTEST_CONTAINER_ID']
        )

    def test_base(self):
        assert self.host.system_info.type == 'linux'
        assert self.host.system_info.distribution == 'alpine'


class TestContainer(object):

    def setup(self):
        self.cont = get_container()

    def test_labels(self):
        assert self.cont.labels['build_tag'] == os.environ[
            'PYTEST_CONTAINER_TAG'
        ]
        assert self.cont.labels['build_time'] == os.environ[
            'PYTEST_CONTAINER_TAG'
        ].split('_')[0]
        assert self.cont.labels['git_commit'].startswith(
            os.environ['PYTEST_CONTAINER_TAG'].split('_')[1]
        )
        assert self.cont.labels['git_url'] == 'git@' \
            'github.com:jantman/private-docker-template.git'
        assert self.cont.labels[
            'maintainer'
        ] == 'Jason Antman <jason@jasonantman.com>'

    def test_mounts(self):
        assert self.cont.attrs['Mounts'] == []

    def test_ports(self):
        assert list(self.cont.attrs['NetworkSettings']['Ports'].keys()) == [
            '80/tcp'
        ]
