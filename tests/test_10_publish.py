import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure
from aifirst10 import Reader
from aifirst10_publish import publish
from test_02_core import manifest, item, catalog, link


class Publish10Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()
        self.output = Path(self.temp.name) / 'output'
        (self.root / 'guide.md').write_text('# Guide\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_migration_is_dry_run_then_writes_new_tree(self):
        (self.root / 'ai.json').write_text(json.dumps(manifest(items=[item()])))
        before = (self.root / 'ai.json').read_bytes()
        report = publish(self.root, self.output)
        self.assertEqual(report['status'], 'preflight-pass')
        self.assertFalse(report['written'])
        self.assertFalse(self.output.exists())
        written = publish(self.root, self.output, apply=True)
        self.assertEqual(written['status'], 'written')
        self.assertEqual((self.root / 'ai.json').read_bytes(), before)
        migrated = json.loads((self.output / 'ai.json').read_text())
        self.assertEqual(migrated['formatVersion'], '1.0')
        reader = Reader(self.output)
        reader.discover(); reader.inventory()
        self.assertEqual(reader.publication()['publication'], 'pass')

    def test_catalog_digest_is_recalculated(self):
        child = catalog([item()])
        raw = json.dumps(child).encode()
        (self.root / 'child.json').write_bytes(raw)
        root = manifest(catalogs=[link(sha256=hashlib.sha256(raw).hexdigest())])
        (self.root / 'ai.json').write_text(json.dumps(root))
        publish(self.root, self.output, apply=True)
        migrated_root = json.loads((self.output / 'ai.json').read_text())
        migrated_child = (self.output / 'child.json').read_bytes()
        self.assertEqual(json.loads(migrated_child)['formatVersion'], '1.0')
        self.assertEqual(migrated_root['catalogs'][0]['sha256'], hashlib.sha256(migrated_child).hexdigest())

    def test_existing_output_and_invalid_source_fail_closed(self):
        (self.root / 'ai.json').write_text(json.dumps(manifest(items=[item()])))
        self.output.mkdir()
        with self.assertRaises(Failure) as error:
            publish(self.root, self.output)
        self.assertEqual(error.exception.code, 'output-exists')
        self.output.rmdir()
        (self.root / 'guide.md').unlink()
        with self.assertRaises(Failure) as error:
            publish(self.root, self.output)
        self.assertEqual(error.exception.code, 'migration-preflight')

    def test_joint_export_derives_llms_txt_from_same_inventory(self):
        value = manifest(formatVersion='1.0', items=[item()])
        (self.root / 'ai.json').write_text(json.dumps(value))
        report = publish(self.root, self.output, apply=True, mode='export')
        self.assertEqual(report['operation'], 'joint-export-1.0')
        llms = (self.output / 'llms.txt').read_text()
        self.assertIn('# Example', llms)
        self.assertIn('[Guide](<guide.md>)', llms)
        self.assertEqual(json.loads((self.output / 'ai.json').read_text())['formatVersion'], '1.0')


if __name__ == '__main__':
    unittest.main()
