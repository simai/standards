import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from aifirst import Failure
from check_candidate10 import ROOT, verify
from check_pilot10 import check, SCENARIOS
from test_10_core import manifest, item


class Receipt10Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root/'ai.json').write_text(json.dumps(manifest(items=[item()])))
        (self.root/'guide.md').write_text('Synthetic receipt unit-test fixture; not a product pilot.')
        (self.root/'log.txt').write_text('Synthetic test evidence, not a product run.')
        self.receipt = {'product': 'docara', 'candidate': '1.0.0-rc.1', 'candidateLockSha256': 'a'*64,
                        'codeRevision': 'b'*40, 'environment': {'runtime': 'synthetic'},
                        'commands': [{'command': 'do not execute this synthetic text', 'exitCode': 0, 'evidence': 'log.txt'}],
                        'publications': ['ai.json'], 'artifacts': [
                            {'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in sorted(self.root.iterdir())],
                        'scenarios': [{'id': name, 'status': 'pass', 'evidence': ['log.txt'], 'notes': 'Synthetic unit-test claim'}
                                      for name in sorted(SCENARIOS['docara'])],
                        'limitations': ['Unit-test fixture only'], 'businessExecution': 'not-run'}

    def tearDown(self): self.temp.cleanup()

    def run_check(self):
        receipt_path = self.root/'receipt.json'; receipt_path.write_text(json.dumps(self.receipt))
        with patch('check_pilot10.verify', return_value={'status': 'pass', 'candidate': '1.0.0-rc.1', 'lockSha256': 'a'*64}):
            return check(receipt_path, self.root)

    def assertCode(self, code):
        with self.assertRaises(Failure) as result: self.run_check()
        self.assertEqual(result.exception.code, code)

    def test_integrity_pass_is_not_automatic_acceptance(self):
        result = self.run_check()
        self.assertEqual(result['publicationCompatibility'], 'pass')
        self.assertEqual(result['pilotAcceptance'], 'pending')
        self.assertFalse(result['commandsExecuted'])

    def test_tampered_material_and_wrong_candidate(self):
        (self.root/'guide.md').write_text('Changed')
        self.assertCode('digest-mismatch')
        self.receipt['candidateLockSha256'] = 'c'*64
        self.assertCode('candidate-mismatch')

    def test_missing_scenario_and_unhashed_evidence(self):
        removed = self.receipt['scenarios'].pop(); self.assertCode('invalid-receipt')
        self.receipt['scenarios'].append(removed)
        self.receipt['commands'][0]['evidence'] = 'unlisted.txt'; self.assertCode('invalid-receipt')

    def test_unlisted_publication_file_and_path_escape(self):
        self.receipt['artifacts'] = [r for r in self.receipt['artifacts'] if r['path'] != 'guide.md']
        self.assertCode('invalid-receipt')
        self.receipt['artifacts'][0]['path'] = '../outside'; self.assertCode('invalid-receipt')

    def test_candidate_verifier_detects_wrong_digest_and_unsafe_path(self):
        for row in ({'path': 'VERSION', 'bytes': 0, 'sha256': '0'*64},
                    {'path': '../outside', 'bytes': 0, 'sha256': '0'*64}):
            lock = self.root/'lock.json'; lock.write_text(json.dumps({'candidate': 'fixture', 'files': [row]}))
            self.assertEqual(verify(lock)['status'], 'fail')
        data = (ROOT/'VERSION').read_bytes()
        lock.write_text(json.dumps({'candidate': 'fixture', 'files': [{'path': 'VERSION', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}))
        self.assertEqual(verify(lock)['status'], 'pass')


if __name__ == '__main__': unittest.main()

