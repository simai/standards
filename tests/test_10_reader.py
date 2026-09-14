import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure
from aifirst10 import PageLinks, Reader, header_links
from aifirst10_transport import Response
from test_10_core import catalog, item, link, manifest


class Reader10Tests(unittest.TestCase):
    def assertCode(self, code, fn):
        with self.assertRaises(Failure) as result:
            fn()
        self.assertEqual(result.exception.code, code)

    def online(self, resources, entry='https://example.test/docs/page'):
        reader = Reader(entry)
        self.calls = []
        def fetch(url, media=None, descriptor=False):
            self.calls.append(url)
            if url not in resources:
                raise Failure('not-found', 'Missing fixture')
            return resources[url]
        reader.transport.fetch = fetch
        return reader

    def test_both_discovery_surfaces_and_conflict(self):
        page = 'https://example.test/docs/page'
        address = 'https://example.test/docs/ai.json'
        html = b'<link rel="describedby" type="application/json" data-ai-first="1.0" href="ai.json">'
        headers = {'link': '<ai.json>; rel="describedby"; type="application/json"; ai-first="1.0"'}
        resources = {page: Response(html, page, headers),
                     address: Response(json.dumps(manifest()).encode(), address, {})}
        reader = self.online(resources)
        reader.discover('page')
        self.assertEqual(reader.base, address)
        headers['link'] = '<different.json>; rel="describedby"; type="application/json"; ai-first="1.0"'
        self.assertCode('ambiguous-discovery', lambda: self.online(resources).discover('page'))

    def test_explicit_manifest_priority_and_final_base(self):
        entry = 'https://example.test/explicit'
        final = 'https://example.test/moved/ai.json'
        resources = {entry: Response(json.dumps(manifest()).encode(), final,
                     {'link': '<conflict>; rel="describedby"; type="application/json"; ai-first="1.0"'})}
        reader = self.online(resources, entry)
        reader.discover('manifest')
        self.assertEqual(self.calls, [entry])
        self.assertEqual(reader.base, final)

    def test_header_parser_preserves_quoted_commas_and_unrelated_links(self):
        value = '<other>; rel="describedby"; type="text/markdown", <ai.json>; title="x,y;z"; rel="alternate describedby"; type="application/json"; ai-first="1.0"'
        self.assertEqual(header_links(value), ['ai.json'])
        self.assertEqual(header_links('<x>; rel="describedby"; type="application/json"'), [])
        self.assertCode('ambiguous-discovery', lambda: header_links(value + '; anchor="/other"'))

    def test_local_read_partial_and_exact_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = '# Example\n\n| Name | Value |\n| --- | --- |\n| Answer | 42 |\n\n```js\nconst answer = 42;\n```\n'
            data = text.encode()
            entry = item(appliesTo={'product': 'urn:product', 'versions': ['1.0']})
            entry['representations'][0]['sha256'] = hashlib.sha256(data).hexdigest()
            (root/'guide.md').write_bytes(data)
            (root/'ai.json').write_text(json.dumps(manifest(items=[entry], catalogs=[link()])))
            reader = Reader(root); reader.discover(); reader.inventory()
            self.assertEqual(reader.select(version='1'), [])
            found = reader.select(version='1.0', product='urn:product')
            result = reader.material(*found[0])
            self.assertEqual(result['text'], text)
            self.assertEqual(result['completeness'], 'partial')
            self.assertEqual(result['errors'][0]['code'], 'not-found')

    def test_fallback_requires_explicit_policy_and_work_identity(self):
        r = Reader('.')
        en = item(1, translationOf='urn:work', language='en')
        fr = item(2, translationOf='urn:work', language='fr')
        r.report = {'items': [(en, 'base'), (fr, 'base')]}
        self.assertEqual(r.select(language='de'), [])
        self.assertCode('invalid-policy', lambda: r.select(language='de', fallback_languages=['fr']))
        found = r.select(language='de', fallback_languages=['fr', 'en'], translation_of='urn:work')
        self.assertEqual(found[0][0]['id'], 'urn:item:2')
        self.assertCode('invalid-policy', lambda: r.select(item_id='urn:item:1', language='de', fallback_languages=['en']))

    def test_routes_cover_page_and_choose_longest_scope(self):
        page = 'https://example.test/docs/api/page'
        top = 'https://example.test/ai.json'
        child = 'https://example.test/docs/api/ai.json'
        root = manifest(routes=[{'scope': 'docs/api/', 'href': 'docs/api/ai.json', 'description': 'API'}])
        resources = {page: Response(b'<html></html>', page, {}),
                     top: Response(json.dumps(root).encode(), top, {}),
                     child: Response(json.dumps(manifest()).encode(), child, {})}
        reader = self.online(resources, page); reader.discover('page')
        self.assertEqual(reader.base, child)
        resources[child] = Response(json.dumps(manifest(resource=dict(manifest()['resource'], scope='../'))).encode(), child, {})
        self.assertCode('scope-mismatch', lambda: self.online(resources, page).discover('page'))

    def test_all_bundled_10_examples_validate(self):
        root = Path(__file__).resolve().parents[1] / 'examples' / '1.0'
        for publication in sorted(path.parent for path in root.glob('*/ai.json')):
            with self.subTest(publication=publication.name):
                reader = Reader(publication)
                reader.discover(); reader.inventory()
                self.assertEqual(reader.publication()['publication'], 'pass')


if __name__ == '__main__':
    unittest.main()
