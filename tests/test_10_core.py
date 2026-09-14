"""Semantic 1.0 cases; 0.1 regression tests run separately and unchanged."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure, structure as structure01
from aifirst02_core import structure as structure02
from aifirst10_core import Inventory, can_skip, check_pin, structure


def item(number=0, **kw):
    value = {'id': f'urn:item:{number}', 'kind': 'knowledge', 'title': 'Guide',
             'description': 'A readable guide', 'language': 'en', 'revision': 'i1',
             'status': 'published', 'source': 'guide.md',
             'representations': [{'href': 'guide.md', 'mediaType': 'text/markdown'}]}
    value.update(kw)
    return value


def manifest(**kw):
    value = {'format': 'ai-first', 'formatVersion': '1.0', 'document': 'manifest',
             'revision': 'root-1', 'resource': {'id': 'urn:test', 'name': 'Example',
             'description': 'Example publication', 'language': 'en', 'scope': './',
             'publisher': {'name': 'Example'}}}
    value.update(kw)
    return value


def catalog(items=None, **kw):
    value = {'format': 'ai-first', 'formatVersion': '1.0', 'document': 'catalog',
             'revision': 'child-1', 'resourceId': 'urn:test', 'items': items or []}
    value.update(kw)
    return value


def link(href='child.json', **kw):
    value = {'href': href, 'description': 'Section', 'revision': 'child-1'}
    value.update(kw)
    return value


class Core10Tests(unittest.TestCase):
    def assertCode(self, code, fn):
        with self.assertRaises(Failure) as result:
            fn()
        self.assertEqual(result.exception.code, code)

    def inventory(self, root, docs, query=None, **limits):
        self.requests = []
        def fetch(url):
            self.requests.append(url)
            if url not in docs:
                raise Failure('not-found', 'Fixture missing')
            return json.dumps(docs[url]).encode(), url
        return Inventory(fetch, urljoin, **limits).walk(root, 'https://example.test/ai.json', query)

    def test_version_handlers_stay_separate(self):
        structure(manifest())
        self.assertCode('unsupported-version', lambda: structure01(manifest()))
        self.assertCode('unsupported-version', lambda: structure02(manifest()))
        old = manifest(formatVersion='0.1')
        structure01(old)
        self.assertCode('unsupported-version', lambda: structure(old))
        previous = manifest(formatVersion='0.2')
        structure02(previous)
        self.assertCode('unsupported-version', lambda: structure(previous))

    def test_pins_required_and_profiles_explicit(self):
        root = manifest(catalogs=[{'href': 'x', 'description': 'x'}])
        self.assertCode('invalid-structure', lambda: structure(root))
        root = manifest(catalogs=[link(select={'languages': ['en']})])
        self.assertCode('missing-profile', lambda: structure(root))
        root['requires'] = ['selective-catalogs']
        structure(root)
        root['catalogs'][0]['select']['languages'] = []
        self.assertCode('invalid-structure', lambda: structure(root))

    def test_independent_revision_and_every_pin(self):
        child = catalog([item()])
        data = json.dumps(child).encode()
        check_pin(link(sha256=hashlib.sha256(data).hexdigest()), child, data, 'urn:test')
        self.assertCode('digest-mismatch', lambda: check_pin(link(sha256='0'*64), child, data, 'urn:test'))
        self.assertCode('resource-mismatch', lambda: check_pin(link(), child, data, 'urn:other'))
        root = manifest(catalogs=[link(), link(revision='wrong')])
        report = self.inventory(root, {'https://example.test/child.json': child})
        self.assertEqual(len(report['items']), 1)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(report['completeness'], 'partial')
        self.assertEqual(report['errors'][0]['code'], 'revision-mismatch')

    def test_unrelated_missing_catalog_retains_material_with_partial_status(self):
        report = self.inventory(manifest(items=[item()], catalogs=[link()]), {})
        self.assertEqual(len(report['items']), 1)
        self.assertEqual(report['completeness'], 'partial')
        self.assertEqual(report['errors'][0]['code'], 'not-found')

    def test_selector_bounds_checked_before_contributing_items(self):
        root = manifest(requires=['selective-catalogs'],
                        catalogs=[link(select={'languages': ['en']})])
        report = self.inventory(root, {'https://example.test/child.json': catalog([item(), item(1, language='fr')])})
        self.assertEqual(report['items'], [])
        self.assertEqual(report['errors'][0]['code'], 'selector-mismatch')

    def test_shared_subtree_rechecks_ancestor_bounds(self):
        root = manifest(requires=['selective-catalogs'], catalogs=[link(), link(select={'languages': ['fr']})])
        report = self.inventory(root, {'https://example.test/child.json': catalog([item()])})
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(report['errors'][0]['code'], 'selector-mismatch')

    def test_unknown_dimension_does_not_skip(self):
        self.assertFalse(can_skip({'languages': ['en']}, {'ids': ['urn:missing']}))
        self.assertFalse(can_skip({'languages': ['EN']}, {'languages': ['en']}))
        self.assertTrue(can_skip({'versions': ['1.0']}, {'versions': ['1']}))

    def test_cycles_and_duplicates(self):
        root = manifest(catalogs=[link()])
        report = self.inventory(root, {'https://example.test/child.json': catalog(catalogs=[link()])})
        self.assertEqual(report['errors'][0]['code'], 'cycle')
        root['items'] = [item()]
        self.assertCode('duplicate-id', lambda: self.inventory(root, {'https://example.test/child.json': catalog([item()])}))

    def test_depth_and_document_limits(self):
        root = manifest(catalogs=[link()])
        for limits in ({'max_depth': 0}, {'max_documents': 0}):
            report = self.inventory(root, {}, **limits)
            self.assertEqual(report['errors'][0]['code'], 'limit-exceeded')
            self.assertEqual(self.requests, [])

    def test_100k_generated_catalog_reads_only_selected_shard(self):
        # 100 shards x 1000 real generated items. Only one is serialized/fetched.
        docs = {}; links = []
        for shard in range(100):
            version = str(shard)
            href = f'shard-{shard}.json'
            links.append(link(href, select={'versions': [version]}))
            docs['https://example.test/' + href] = catalog([
                item(shard*1000+n, appliesTo={'product': 'urn:product', 'versions': [version]})
                for n in range(1000)])
        self.assertEqual(sum(len(d['items']) for d in docs.values()), 100000)
        report = self.inventory(manifest(requires=['selective-catalogs'], catalogs=links),
                                docs, {'versions': ['42']})
        self.assertEqual(self.requests, ['https://example.test/shard-42.json'])
        self.assertEqual(len(report['items']), 1000)
        self.assertEqual(len(report['omittedCatalogs']), 99)
        self.assertEqual(report['completeness'], 'targeted')
        self.assertEqual(report['errors'], [])

    def test_translation_and_access_profile_requirements(self):
        root = manifest(items=[item(translationOf='urn:work')])
        self.assertCode('missing-profile', lambda: structure(root))
        root['requires'] = ['translations', 'protected-reading']
        root['access'] = {'required': True, 'description': 'Use the existing sign-in mechanism'}
        structure(root)
        root['access']['token'] = 'forbidden-placeholder'
        self.assertCode('invalid-structure', lambda: structure(root))

    def test_yaml_media_is_only_for_openapi(self):
        cap = {'contract': {'type': 'openapi', 'href': 'api.yaml', 'mediaType': 'application/yaml',
                           'operation': '/paths/~1settings/get'},
               'effects': 'read', 'authorization': 'required', 'confirmation': 'not-required',
               'instructions': 'usage.md'}
        root = manifest(items=[item(kind='capability', capability=cap)])
        structure(root)
        cap['contract']['type'] = 'mcp'
        self.assertCode('invalid-contract', lambda: structure(root))


if __name__ == '__main__':
    unittest.main()
