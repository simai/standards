import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_release import verify
import check_candidate10

class ReleaseTests(unittest.TestCase):
    def test_release_detects_modified_and_missing_input(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); p = root/'rules.md'; p.write_bytes(b'rules')
            lock = {'release':'1.1.1', 'standards':{'ai-first':'1.0.0','standard-contract':'1.0.0','standard-contract-lifecycle':'1.0.0','simai.linkage':'1.1.0','simai.change-lifecycle':'1.1.0'}, 'files':[{'path':'rules.md','bytes':5,'sha256':hashlib.sha256(b'rules').hexdigest()}]}
            (root/'release-manifest.json').write_text(json.dumps(lock))
            self.assertEqual(verify(root)['status'], 'pass')
            p.write_bytes(b'other'); self.assertEqual(verify(root)['status'], 'fail')
            p.unlink(); self.assertEqual(verify(root)['status'], 'fail')

    def test_archive_does_not_fall_back_to_current_bytes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); (root/'conformance/1.0').mkdir(parents=True)
            (root/'VERSION').write_bytes(b'historical')
            row = {'path':'VERSION','bytes':10,'sha256':hashlib.sha256(b'historical').hexdigest()}
            (root/'conformance/1.0/candidate.json').write_text(json.dumps({'candidate':'1.0.0-rc.1','files':[row]}))
            with patch.object(check_candidate10, 'ROOT', root):
                self.assertEqual(check_candidate10.verify()['status'], 'fail')
                archive=root/'archives/1.0-candidate'; archive.mkdir(parents=True)
                (archive/'VERSION').write_bytes(b'historical')
                self.assertEqual(check_candidate10.verify()['status'], 'pass')
