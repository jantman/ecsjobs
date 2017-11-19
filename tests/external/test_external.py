from ecsbuild.test_helpers import *


class TestFoo(HTTPTestBase):

    hostname = 'foo.jasonantman.com'
    logpath = '/var/log/nginx/foo.jasonantman.com.access.log'

    def test_base(self, host):
        path = '/'
        self.assert_redirect_to(
            path, 'http://github.com/jantman'
        )
        self.assert_access_log(path)

    def test_deep_url(self, host):
        path = '/cgi-bin/viewvc.cgi/nagios-xml/foo'
        self.assert_redirect_to(
            path, 'http://github.com/jantman'
        )
        self.assert_access_log(path)

    def test_base_path(self, host):
        src_path = os.path.abspath(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..', '..', 'content', 'www.jasonantman.com', 'index.html'
        ))
        with open(src_path, 'rb') as fh:
            src_content = fh.read()
        url = '%s/' % self.url
        site = 'http://%s/' % self.hostname
        r = self.request_url(url)
        assert r.status_code == 200, 'Expected "%s" to return 200 but ' \
            'returned %s' % (site, r.status_code)
        assert r.content == src_content
