import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure
from aifirst02 import Reader
from aifirst02_contracts import parse_contract, validate_contract
from aifirst02_transport import Transport
from test_02_core import item, manifest


def operation_item(media='application/json', href='openapi.json', operation='/paths/~1settings/get'):
    return item(kind='capability', capability={
        'contract': {'type': 'openapi', 'href': href, 'mediaType': media, 'operation': operation},
        'effects': 'read', 'authorization': 'required', 'confirmation': 'not-required',
        'instructions': 'guide.md'})


def api(version='3.0.4'):
    return {'openapi': version, 'info': {'title': 'Fixture', 'version': '1'},
            'paths': {'/settings': {'get': {'responses': {'200': {'description': 'Settings'}}}}}}


class Contract02Tests(unittest.TestCase):
    def assertCode(self, code, fn):
        with self.assertRaises(Failure) as result: fn()
        self.assertEqual(result.exception.code, code)

    def validate(self, document, entry=None, others=None):
        entry = entry or operation_item()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'guide.md').write_text('Read-only documentation')
            c = entry['capability']['contract']
            raw = json.dumps(document) if c['mediaType'] == 'application/json' else yaml.safe_dump(document)
            (root/c['href']).write_text(raw)
            for name, contents in (others or {}).items(): (root/name).write_text(contents)
            t = Transport(root)
            result = validate_contract(t, entry, (root/'ai.json').as_uri())
            self.assertTrue(all(not r['url'].endswith('/settings') for r in t.records))
            return result

    def test_all_supported_versions_json_and_yaml(self):
        for version in ('3.0.4', '3.1.2', '3.2.0'):
            for media in ('application/json', 'application/yaml', 'text/yaml', 'application/x-yaml'):
                with self.subTest(version=version, media=media):
                    result = self.validate(api(version), operation_item(media))
                    self.assertEqual(result['binding'], 'pass')
                    self.assertEqual(result['businessExecution'], 'not-run')
                    self.assertEqual(result['fullContractValidation'], 'not-run')

    def test_version_and_locator_errors(self):
        self.assertCode('invalid-contract', lambda: self.validate(api('3.3.0')))
        self.assertCode('invalid-contract', lambda: self.validate(api(), operation_item(operation='/paths/~1missing/get')))
        self.assertCode('invalid-contract', lambda: self.validate(api(), operation_item(operation='/paths/~2settings/get')))

    def test_refs_reuse_existing_contracts(self):
        doc = api(); target = doc['paths']['/settings']; doc['paths']['/settings'] = {'$ref': '#/components/pathItems/settings'}
        doc['components'] = {'pathItems': {'settings': target}}
        self.assertEqual(self.validate(doc)['binding'], 'pass')
        doc['paths']['/settings'] = {'$ref': 'path.yaml'}
        self.assertEqual(self.validate(doc, others={'path.yaml': yaml.safe_dump(target)})['binding'], 'pass')
        doc['paths']['/settings'] = {'$ref': '#/paths/~1settings'}
        self.assertCode('cycle', lambda: self.validate(doc))

    def test_32_methods_and_optional_responses(self):
        doc = api('3.2.0')
        doc['paths']['/settings']['query'] = {}
        doc['paths']['/settings']['additionalOperations'] = {'COPY': {}}
        for locator in ('/paths/~1settings/query', '/paths/~1settings/additionalOperations/COPY'):
            self.assertEqual(self.validate(doc, operation_item(operation=locator))['binding'], 'pass')
        doc = api('3.0.4'); doc['paths']['/settings']['get'] = {}
        self.assertCode('invalid-contract', lambda: self.validate(doc))

    def test_yaml_rejects_unsafe_or_ambiguous_input(self):
        bad = [b'a: 1\na: 2', b'a: !!python/object:os.system {}', b'200: x',
               b'a: .nan', b'a: 1\n---\nb: 2', b'a: &a [*a]', b'a: !!binary eA==']
        for data in bad:
            with self.subTest(data=data):
                self.assertCode('invalid-contract', lambda: parse_contract(data, 'application/yaml'))
        self.assertCode('limit-exceeded', lambda: parse_contract(('['*70+']'*70).encode(), 'application/yaml'))
        bomb = 'a: &a [1,1,1,1,1,1,1,1,1,1]\n'
        for i in range(6):
            previous = 'a' if i == 0 else 'n'+str(i-1)
            bomb += 'n'+str(i)+': &n'+str(i)+' ['+','.join(['*'+previous]*10)+']\n'
        self.assertCode('limit-exceeded', lambda: parse_contract(bomb.encode(), 'application/yaml'))
        self.assertEqual(parse_contract(b'a: &a [1, 2]\nb: *a', 'application/yaml')['b'], [1, 2])
        self.assertEqual(parse_contract(b'title: on', 'application/yaml')['title'], 'on')

    def test_full_publication_fails_on_broken_material_and_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); entry = operation_item()
            (root/'ai.json').write_text(json.dumps(manifest(items=[entry])))
            reader = Reader(root); reader.discover(); reader.inventory()
            result = reader.publication()
            self.assertEqual(result['publication'], 'fail')
            self.assertIn('contract', [e['role'] for e in result['errors']])
            (root/'guide.md').write_text('Guide')
            (root/'openapi.json').write_text(json.dumps(api()))
            reader = Reader(root); reader.discover(); reader.inventory()
            result = reader.publication()
            self.assertEqual(result['publication'], 'pass')
            self.assertEqual(result['contractLocators'][0]['binding'], 'pass')


if __name__ == '__main__': unittest.main()
