import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure, Reader as Reader01
from aifirst02 import Reader
from aifirst02_publish import publish
from test_02_core import manifest, item, catalog, link


class Publish02Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root/'source'; self.source.mkdir()
        self.output = self.root/'output'

    def tearDown(self): self.temp.cleanup()

    def write(self, name, data):
        p = self.source/name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data) if isinstance(data, dict) else data)

    def assertCode(self, code, fn):
        with self.assertRaises(Failure) as result: fn()
        self.assertEqual(result.exception.code, code)

    def fixture(self, version='0.1'):
        self.write('guide.md', '# Guide\n\n```python\nprint(42)\n```\n')
        self.write('ai.json', manifest(formatVersion=version, items=[item()]))

    def test_dry_run_then_new_output_preserves_source(self):
        self.fixture()
        before = (self.source/'ai.json').read_bytes()
        result = publish(self.source, self.output, 'migrate')
        self.assertFalse(result['written']); self.assertFalse(self.output.exists())
        self.assertTrue(result['manualReview'])
        result = publish(self.source, self.output, 'migrate', apply=True)
        self.assertTrue(result['written'])
        self.assertEqual((self.source/'ai.json').read_bytes(), before)
        old = Reader01(self.source); old.discover(); old.inventory()
        new = Reader(self.output); new.discover(); new.inventory()
        self.assertEqual(new.publication()['publication'], 'pass')
        self.assertEqual(old.material(*old.items[0])['text'], new.material(*new.report['items'][0])['text'])
        self.assertCode('output-exists', lambda: publish(self.source, self.output, 'migrate', apply=True))

    def test_nested_catalog_pins_and_unreferenced_secret_exclusion(self):
        self.fixture()
        self.write('ai.json', manifest(formatVersion='0.1', revision='snapshot', catalogs=[{'href':'child.json', 'description':'Child'}]))
        self.write('child.json', catalog([item()], formatVersion='0.1', revision='snapshot'))
        self.write('.env', 'TEST_ONLY_DO_NOT_COPY=fixture')
        publish(self.source, self.output, 'migrate', apply=True)
        self.assertFalse((self.output/'.env').exists())
        root = json.loads((self.output/'ai.json').read_text())
        pin = root['catalogs'][0]
        self.assertEqual(pin['revision'], 'snapshot')
        self.assertEqual(pin['sha256'], hashlib.sha256((self.output/'child.json').read_bytes()).hexdigest())

    def test_preflight_failure_leaves_no_output(self):
        self.fixture(); (self.source/'guide.md').unlink()
        self.assertCode('migration-preflight', lambda: publish(self.source, self.output, 'migrate', apply=True))
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.ai-first-stage-*')), [])

    def test_unknown_optional_semantic_collision_requires_review(self):
        self.fixture(); self.write('ai.json', manifest(formatVersion='0.1', items=[item(translationOf='urn:work')]))
        self.assertCode('migration-collision', lambda: publish(self.source, self.output, 'migrate'))

    def test_joint_export_one_source_preserves_code_and_omits_removed_item(self):
        self.fixture('0.2')
        self.write('removed.md', 'Old unreferenced material')
        publish(self.source, self.output, 'export', apply=True)
        self.assertEqual((self.source/'guide.md').read_bytes(), (self.output/'guide.md').read_bytes())
        self.assertIn('[Guide](<guide.md>)', (self.output/'llms.txt').read_text())
        self.assertFalse((self.output/'removed.md').exists())
        self.assertEqual((self.source/'ai.json').read_bytes(), (self.output/'ai.json').read_bytes())

    def test_existing_llms_requires_reconciliation(self):
        self.fixture('0.2'); self.write('llms.txt', 'Existing handwritten content')
        self.assertCode('export-collision', lambda: publish(self.source, self.output, 'export'))

    def test_overlap_and_destination_symlink_rejected(self):
        self.fixture()
        self.assertCode('invalid-output', lambda: publish(self.source, self.source/'out', 'migrate'))
        self.output.symlink_to(self.source, target_is_directory=True)
        self.assertCode('output-exists', lambda: publish(self.source, self.output, 'migrate'))

    def test_staging_error_preserves_previous_result(self):
        self.fixture('0.2'); self.output.mkdir(); (self.output/'old.txt').write_text('Keep')
        self.assertCode('output-exists', lambda: publish(self.source, self.output, 'export', apply=True))
        self.assertEqual((self.output/'old.txt').read_text(), 'Keep')
        output2 = self.root/'new'
        with patch('aifirst02_publish.Reader02.publication', side_effect=Failure('fixture-error', 'Failure')):
            self.assertCode('fixture-error', lambda: publish(self.source, output2, 'export', apply=True))
        self.assertFalse(output2.exists())


if __name__ == '__main__': unittest.main()
