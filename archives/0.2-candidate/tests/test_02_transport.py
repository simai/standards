import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure, Limits
from aifirst02_transport import Transport


class Handler(BaseHTTPRequestHandler):
    observations = []
    cross_target = None
    def log_message(self, *args):
        pass
    def do_GET(self):
        Handler.observations.append((self.path, self.headers.get('Authorization'),
                                     self.headers.get('If-None-Match')))
        data = b'# Documentation\n\n```python\nprint(42)\n```\n'
        status = 200; extra = {}; media = 'text/markdown'
        if self.path in ('/page', '/conflict'):
            data = b'<link rel="describedby" type="application/json" data-ai-first="0.2" href="ai.json">'
            media = 'text/html'
            target = 'other.json' if self.path == '/conflict' else 'ai.json'
            extra['Link'] = '<'+target+'>; rel="describedby"; type="application/json"; ai-first="0.2"'
        elif self.path == '/ai.json':
            from test_02_core import manifest, item
            data = json.dumps(manifest(items=[item()])).encode(); media = 'application/json'
        elif self.path == '/cross':
            status = 302; extra['Location'] = Handler.cross_target
        elif self.path == '/redirect':
            status = 302; extra['Location'] = '/gzip'
        elif self.path == '/loop':
            status = 307; extra['Location'] = '/loop'
        elif self.path == '/downgrade':
            status = 302; extra['Location'] = 'http://localhost:9/no'
        elif self.path == '/outside':
            status = 302; extra['Location'] = 'https://example.invalid/no'
        elif self.path == '/gzip':
            data = gzip.compress(data); extra['Content-Encoding'] = 'gzip'
        elif self.path == '/bomb':
            data = gzip.compress(b'x'*100000); extra['Content-Encoding'] = 'gzip'
        elif self.path == '/truncated':
            data = gzip.compress(data)[:-4]; extra['Content-Encoding'] = 'gzip'
        elif self.path == '/trailing':
            data = gzip.compress(data) + b'extra'; extra['Content-Encoding'] = 'gzip'
        elif self.path == '/unsupported':
            extra['Content-Encoding'] = 'br'
        elif self.path == '/orphan304':
            status = 304
        elif self.path in ('/cache', '/nostore', '/private'):
            if self.path == '/private':
                if not self.headers.get('Authorization'):
                    status = 401
                data = self.headers.get('Authorization', 'denied').encode()
            extra['ETag'] = '"v1"'
            extra['Cache-Control'] = 'no-store' if self.path == '/nostore' else 'no-cache, private'
            if status == 200 and self.headers.get('If-None-Match') == '"v1"':
                status = 304; data = b''
        self.send_response(status)
        self.send_header('Content-Type', media)
        for k, v in extra.items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Transport02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name)
        key = cls.path/'key.pem'; cert = cls.path/'cert.pem'
        # Ephemeral local trust anchor; keys never leave this temporary directory.
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(key), '-out', str(cert), '-days', '1',
                        '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.base = 'https://localhost:' + str(cls.server.server_port)
        cls.cert = str(cert)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        cls.temp.cleanup()

    def setUp(self):
        Handler.observations = []

    def client(self, **kwargs):
        return Transport(self.base, allow_loopback=True, ca_file=self.cert, **kwargs)

    def assertCode(self, code, fn):
        with self.assertRaises(Failure) as result:
            fn()
        self.assertEqual(result.exception.code, code)

    def test_tls_trust_required_and_hostname_checked(self):
        self.assertCode('tls-error', lambda: Transport(self.base, allow_loopback=True).fetch(self.base+'/gzip'))
        wrong = self.base.replace('localhost', '127.0.0.1')
        self.assertCode('tls-error', lambda: Transport(wrong, allow_loopback=True, ca_file=self.cert).fetch(wrong+'/gzip'))
        self.assertTrue(self.client().fetch(self.base+'/gzip').data.startswith(b'# Documentation'))

    def test_redirect_gzip_provenance(self):
        t = self.client()
        response = t.fetch(self.base+'/redirect', 'text/markdown')
        self.assertEqual(response.url, self.base+'/gzip')
        self.assertEqual(t.records[0]['sha256'], hashlib.sha256(response.data).hexdigest())
        self.assertEqual(t.records[0]['url'], self.base+'/redirect')
        self.assertEqual(len(Handler.observations), 2)

    def test_redirect_boundaries(self):
        for path, code in (('/loop', 'cycle'), ('/downgrade', 'access-blocked'),
                           ('/outside', 'access-blocked')):
            self.assertCode(code, lambda: self.client().fetch(self.base+path))
        self.assertCode('limit-exceeded', lambda: self.client(max_redirects=0).fetch(self.base+'/redirect'))

    def test_expansion_truncation_and_encoding(self):
        self.assertCode('limit-exceeded', lambda: self.client(limits=Limits(material_bytes=1024)).fetch(self.base+'/bomb'))
        for path in ('/truncated', '/trailing'):
            self.assertCode('invalid-encoding', lambda: self.client().fetch(self.base+path))
        self.assertCode('unsupported-encoding', lambda: self.client().fetch(self.base+'/unsupported'))

    def test_cache_revalidation_and_no_store(self):
        t = self.client()
        first = t.fetch(self.base+'/cache', 'text/markdown')
        second = t.fetch(self.base+'/cache', 'text/markdown')
        self.assertEqual(first.data, second.data)
        self.assertEqual(second.cache, 'revalidated')
        self.assertEqual(t.records[-1]['transferredBytes'], 0)
        self.assertEqual(Handler.observations[-1][2], '"v1"')
        t.fetch(self.base+'/nostore'); t.fetch(self.base+'/nostore')
        self.assertIsNone(Handler.observations[-1][2])
        self.assertCode('invalid-cache', lambda: t.fetch(self.base+'/orphan304'))

    def test_credentials_scope_rotation_and_denied_access(self):
        current = {'authorization': 'Bearer fixture-A'}
        t = self.client(credential_provider=lambda url: current,
                        credential_scopes=[self.base+'/private'], principal='fixture-user')
        a = t.fetch(self.base+'/private')
        current['authorization'] = 'Bearer fixture-B'
        b = t.fetch(self.base+'/private')
        self.assertNotEqual(a.data, b.data)
        self.assertIsNone(Handler.observations[-1][2])
        t.fetch(self.base+'/cache')
        self.assertIsNone(Handler.observations[-1][1])
        self.assertNotIn('fixture-A', json.dumps(t.records))
        self.assertNotIn('fixture-B', json.dumps(t.records))
        self.assertCode('access-denied', lambda: self.client().fetch(self.base+'/private'))

    def test_javascript_and_python_https_discovery_read(self):
        node = os.environ.get('AI_FIRST_NODE')
        if not node:
            self.skipTest('Set AI_FIRST_NODE to verify the JavaScript HTTPS baseline')
        from aifirst02 import Reader
        reader = Reader(self.base+'/page', allow_loopback=True, ca_file=self.cert)
        reader.discover('page'); reader.inventory()
        expected = reader.material(*reader.select()[0])
        script = Path(__file__).resolve().parents[1]/'tools/aifirst02.mjs'
        for page in ('/page', '/conflict'):
            result = subprocess.run([node, str(script), 'read', self.base+page, '--mode', 'page',
                                     '--allow-loopback', '--ca-file', self.cert], capture_output=True, text=True)
            actual = json.loads(result.stdout)
            if page == '/conflict':
                self.assertEqual(actual['error']['code'], 'ambiguous-discovery')
            else:
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                for key in ('id', 'text', 'sha256', 'source', 'representation'):
                    self.assertEqual(expected[key], actual[key])

    def test_credentials_are_not_forwarded_to_an_allowed_other_origin(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert, self.path/'key.pem')
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        other = 'https://localhost:' + str(server.server_port)
        Handler.cross_target = other + '/cache'
        try:
            t = self.client(allow_origins=[other], credential_provider=lambda url: {'authorization': 'Bearer fixture'},
                            credential_scopes=[self.base+'/'], principal='user')
            t.fetch(self.base+'/cross')
            self.assertEqual(Handler.observations[0][1], 'Bearer fixture')
            self.assertIsNone(Handler.observations[1][1])
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_ambiguous_paths_do_not_receive_credentials(self):
        t = self.client(credential_provider=lambda url: {'authorization': 'Bearer fixture'},
                        credential_scopes=[self.base+'/private'], principal='user')
        for suffix in ('/private/%2e%2e/cache', '/private/../cache', '/private/%2fcache', '/private/%00x'):
            self.assertCode('access-blocked', lambda: t.fetch(self.base+suffix))
        self.assertEqual(Handler.observations, [])

    def test_local_path_and_symlink_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'safe').mkdir()
            (root/'outside.txt').write_text('outside')
            (root/'safe/link.txt').symlink_to(root/'outside.txt')
            t = Transport(root/'safe')
            self.assertCode('access-blocked', lambda: t.fetch((root/'safe/link.txt').as_uri()))
            self.assertCode('access-blocked', lambda: t.fetch((root/'outside.txt').as_uri()))

    def test_private_network_requires_explicit_caller_policy(self):
        self.assertCode('access-blocked', lambda: Transport(self.base, ca_file=self.cert).fetch(self.base+'/gzip'))
        t = Transport(self.base, ca_file=self.cert, allow_networks=['127.0.0.0/8', '::1/128'])
        self.assertTrue(t.fetch(self.base+'/gzip').data)


if __name__ == '__main__':
    unittest.main()
