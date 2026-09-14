import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst10 import Reader


PRIVATE_ID = 'urn:fixture:private-validator'


def item(identifier, href, title):
    return {'id': identifier, 'kind': 'knowledge', 'title': title,
            'description': title, 'language': 'en', 'revision': '1',
            'status': 'published', 'source': href,
            'representations': [{'href': href, 'mediaType': 'text/markdown'}]}


def manifest(operator):
    items = [item('urn:fixture:public', 'public.md', 'Public guide')]
    if operator:
        items.append(item(PRIVATE_ID, 'private.md', 'Private validation guide'))
    return {'format': 'ai-first', 'formatVersion': '1.0', 'document': 'manifest',
            'revision': 'operator-1' if operator else 'public-1',
            'requires': ['protected-reading'],
            'resource': {'id': 'urn:fixture:filtered', 'name': 'Filtered fixture',
                         'description': 'Actor-filtered publication', 'language': 'en',
                         'scope': './', 'publisher': {'name': 'Fixture'}},
            'access': {'required': operator, 'description': 'Use existing access'},
            'items': items}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        operator = self.headers.get('Authorization') == 'Bearer operator'
        status = 200
        media = 'application/json' if self.path == '/ai.json' else 'text/markdown'
        if self.path == '/ai.json':
            data = json.dumps(manifest(operator)).encode()
        elif self.path == '/public.md':
            data = b'# Public guide\n'
        elif self.path == '/private.md' and operator:
            data = b'# Private validation guide\n'
        else:
            status = 403
            data = b'denied'
        self.send_response(status)
        self.send_header('Content-Type', media)
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Security10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        key = root / 'key.pem'
        cert = root / 'cert.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(key), '-out', str(cert), '-days', '1',
                        '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'https://localhost:{cls.server.server_port}/'
        cls.cert = str(cert)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def reader(self, operator=False):
        policy = {'allow_loopback': True, 'ca_file': self.cert,
                  'principal': 'operator' if operator else 'public'}
        if operator:
            policy.update(credential_provider=lambda url: {'authorization': 'Bearer operator'},
                          credential_scopes=[self.base])
        reader = Reader(self.base, **policy)
        reader.discover()
        reader.inventory()
        return reader

    def test_public_projection_never_receives_private_identity_or_location(self):
        reader = self.reader(False)
        result = reader.material(*reader.select()[0])
        visible = json.dumps({'manifest': reader.manifest, 'result': result,
                              'provenance': reader.transport.records})
        self.assertNotIn(PRIVATE_ID, visible)
        self.assertNotIn('private.md', visible)
        self.assertNotIn('Bearer operator', visible)
        self.assertEqual(result['text'], '# Public guide\n')

    def test_operator_projection_and_cache_context_are_separate(self):
        public = self.reader(False)
        operator = self.reader(True)
        self.assertEqual([row[0]['id'] for row in public.report['items']], ['urn:fixture:public'])
        self.assertEqual({row[0]['id'] for row in operator.report['items']},
                         {'urn:fixture:public', PRIVATE_ID})
        private = operator.select(item_id=PRIVATE_ID)[0]
        self.assertEqual(operator.material(*private)['text'], '# Private validation guide\n')
        self.assertIsNot(public.transport.cache, operator.transport.cache)
        self.assertNotIn('Bearer operator', json.dumps(operator.transport.records))


if __name__ == '__main__':
    unittest.main()
