"""simai.linkage 1.1.0 and simai.change-lifecycle 1.1.0: envelopes, formats and the reference implementation."""
import copy
import hashlib
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
STANDARDS = ROOT / 'standards'
sys.path.insert(0, str(STANDARDS))
import linkage  # noqa: E402

EX = STANDARDS / 'examples'
STANDARD_FILES = [STANDARDS / 'simai.linkage/1.1.0/standard.json', STANDARDS / 'simai.change-lifecycle/1.1.0/standard.json']


def load(path):
    return json.loads(Path(path).read_text())


class Envelopes(unittest.TestCase):
    def test_envelope_is_standard_contract_1_0(self):
        schema = load(ROOT / 'standard-contract/1.0/standard.schema.json')
        for path in STANDARD_FILES:
            errors = [e.message for e in Draft202012Validator(schema).iter_errors(load(path))]
            self.assertEqual([], errors, path)

    def test_pins_match_files(self):
        for path in STANDARD_FILES:
            doc = load(path)
            for pin in [*doc['uses'], *doc['references'], doc['specification']]:
                if 'path' not in pin:
                    continue
                data = (path.parent / pin['path']).resolve().read_bytes()
                self.assertEqual(pin['sha256'], hashlib.sha256(data).hexdigest(), f"{path.name}: {pin['path']}")

    def test_requirement_ids_unique(self):
        for path in STANDARD_FILES:
            ids = [r['id'] for r in load(path)['requirements']]
            self.assertEqual(len(ids), len(set(ids)), path)

    def test_framework_requirements_kept(self):
        # Every 1.0.0 linkage requirement keeps its id; renamed lifecycle ones say so in guidance.
        linkage_ids = {r['id'] for r in load(STANDARD_FILES[0])['requirements']}
        for rid in ['every-unit-has-a-passport', 'id-never-changes', 'content-hash', 'hash-moves-version', 'dependencies-declared',
                    'inventory-per-release', 'inventory-is-complete', 'inventories-compare', 'journal-per-version',
                    'consumer-keeps-a-record', 'record-is-local-data', 'foundations-count', 'one-reconcile', 'report-is-data',
                    'no-silent-drift', 'gate-in-the-release', 'one-format-for-all-sources', 'adopt-in-place']:
            self.assertIn(rid, linkage_ids)
        guidance = ' '.join(r.get('guidance', '') for r in load(STANDARD_FILES[1])['requirements'])
        for old in ['one-version-line', 'no-alias-without-record', 'sweep-on-schedule', 'runtime-notes-use', 'consumers-scanned-before-sweep']:
            self.assertIn(f'1.0.0 id {old}', guidance)

    def test_schemas_are_valid(self):
        for path in [*(STANDARDS / 'schemas').glob('*.json'), *(STANDARDS / 'pinned').glob('*.json')]:
            Draft202012Validator.check_schema(load(path))


class Formats(unittest.TestCase):
    def test_examples_validate(self):
        paths = sorted(EX.rglob('*.json'))
        self.assertGreaterEqual(len(paths), 9)
        for path in paths:
            self.assertEqual([], linkage.validate(load(path)), path)

    def test_framework_passport_read_as_core(self):
        doc = load(EX / 'framework/accordion.passport.json')
        self.assertEqual('framework', linkage.profile_of(doc)['id'])
        self.assertEqual('1.0.0', linkage.profile_of(doc)['version'])

    def test_core_passport_needs_profile(self):
        doc = load(EX / 'templates/loan.passport.json')
        del doc['profile']
        self.assertNotEqual([], linkage.validate(doc))

    def test_normalized_text_needs_rule(self):
        doc = load(EX / 'norms/gk-809.passport.json')
        doc.pop('normalization', None)
        self.assertNotEqual([], linkage.validate(doc))


class Hashes(unittest.TestCase):
    def test_normalized_text(self):
        self.assertEqual(linkage.hash_normalized_text('  free\n\nloan '), linkage.hash_normalized_text('free loan'))
        self.assertNotEqual(linkage.hash_normalized_text('a b'), linkage.hash_normalized_text('a  c'))
        # NFC: a decomposed letter hashes like the composed one.
        self.assertEqual(linkage.hash_normalized_text('\u0438\u0306'), linkage.hash_normalized_text('\u0439'))

    def test_git_files_reads_committed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = lambda *a: subprocess.run(['git', '-C', tmp, *a], check=True, capture_output=True)
            git('init', '-q')
            (Path(tmp) / 'b.txt').write_bytes(b'yy')
            (Path(tmp) / 'a.txt').write_bytes(b'x')
            git('add', '.')
            git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-qm', 't')
            (Path(tmp) / 'a.txt').write_bytes(b'changed in the working tree')
            expected = hashlib.sha256(b'a.txt\x001\x00x' + b'b.txt\x002\x00yy').hexdigest()
            self.assertEqual(expected, linkage.hash_git_files(['b.txt', 'a.txt'], tmp))

    def test_step(self):
        self.assertEqual('major', linkage.step('1.2.3', '2.0.0'))
        self.assertEqual('minor', linkage.step('1.2.3', '1.3.0'))
        self.assertEqual('patch', linkage.step('1.2.3', '1.2.4'))


class Compare(unittest.TestCase):
    def setUp(self):
        self.a = load(EX / 'framework/inventory-a.json')
        self.b = load(EX / 'framework/inventory-b.json')

    def test_changes_and_dependants(self):
        report = linkage.compare(self.a, self.b)
        self.assertEqual([], report['violations'])
        self.assertEqual(['tokens.colour'], [c['id'] for c in report['changed']])
        self.assertIn('component.accordion', [d['id'] for d in report['dependencies_changed']])
        self.assertEqual([], linkage.validate(report))

    def test_hash_moved_without_version(self):
        b = copy.deepcopy(self.a)
        b['units'][0]['content_sha256'] = 'f' * 64
        codes = [v['code'] for v in linkage.compare(self.a, b)['violations']]
        self.assertEqual(['hash-moved-without-version'], codes)

    def test_version_went_back(self):
        b = copy.deepcopy(self.b)
        a = copy.deepcopy(self.b)
        for u in a['units']:
            if u['id'] == 'tokens.colour':
                u['version'] = '9.0.0'
        self.assertIn('version-went-back', [v['code'] for v in linkage.compare(a, b)['violations']])

    def test_source_differs(self):
        b = copy.deepcopy(self.b)
        b['source'] = 'someone/else'
        self.assertIn('source-differs', [v['code'] for v in linkage.compare(self.a, b)['violations']])


class Reconcile(unittest.TestCase):
    def documents(self, as_of, record=None):
        record = record or load(EX / 'documents/usage-record.json')
        report = linkage.reconcile(record, [load(EX / 'templates/inventory.json'), load(EX / 'norms/inventory.json')], as_of=as_of)
        self.assertEqual([], linkage.validate(report))
        return {p['place']: p for p in report['places']}

    def test_framework_foundation_counts(self):
        record = load(EX / 'framework/usage-record.json')
        report = linkage.reconcile(record, [load(EX / 'framework/inventory-b.json')], as_of='2026-11-02',
                                   baselines=[load(EX / 'framework/inventory-a.json')])
        place = report['places'][0]
        self.assertEqual('update-available', place['status'])
        self.assertEqual('tokens.colour', place['path'][0])
        self.assertEqual([], linkage.validate(report))

    def test_framework_current_without_baseline_change(self):
        record = load(EX / 'framework/usage-record.json')
        report = linkage.reconcile(record, [load(EX / 'framework/inventory-a.json')], as_of='2026-11-02',
                                   baselines=[load(EX / 'framework/inventory-a.json')])
        self.assertEqual('current', report['places'][0]['status'])

    def test_unchecked_norm_is_unverified_today(self):
        self.assertEqual('unverified', self.documents('2026-11-02')['contract 15/2026']['status'])

    def test_mandatory_restated_norm_needs_action_after_new_edition(self):
        place = self.documents('2027-04-01')['contract 15/2026']
        self.assertEqual('action-needed', place['status'])
        self.assertIn('ru/gk/808', place['path'][0])

    def test_signed_contract_is_kept(self):
        # An unchecked norm still shows through kept: unverified ranks above it.
        self.assertEqual('unverified', self.documents('2027-04-01')['contract 16/2026 (signed)']['status'])
        norms = load(EX / 'norms/inventory.json')
        for u in norms['units']:
            u['checked'] = '2026-11-02'
        report = linkage.reconcile(load(EX / 'documents/usage-record.json'), [load(EX / 'templates/inventory.json'), norms], as_of='2027-04-01')
        places = {p['place']: p['status'] for p in report['places']}
        self.assertEqual({'contract 15/2026': 'action-needed', 'contract 16/2026 (signed)': 'kept'}, places)

    def test_upcoming_edition_reported(self):
        norms = load(EX / 'norms/inventory.json')
        for u in norms['units']:
            u['checked'] = '2026-11-02'
        record = load(EX / 'documents/usage-record.json')
        report = linkage.reconcile(record, [load(EX / 'templates/inventory.json'), norms], as_of='2026-11-02')
        self.assertEqual('upcoming', report['places'][0]['status'])

    def test_missing_unit(self):
        record = load(EX / 'documents/usage-record.json')
        record['places'][0]['unit'] = 'ru/lease'
        self.assertEqual('missing', self.documents('2026-11-02', record)['contract 15/2026']['status'])


class AnchorsAndRepeal(unittest.TestCase):
    def setUp(self):
        self.templates = load(EX / 'templates/inventory.json')
        self.norms = load(EX / 'norms/inventory.json')
        for u in self.norms['units']:
            u['checked'] = '2026-11-02'
        self.record = load(EX / 'documents/usage-record.json')
        self.record['places'] = self.record['places'][:1]

    def statuses(self, anchor, as_of):
        place = self.record['places'][0]
        place['anchor'] = anchor
        return linkage.reconcile(self.record, [self.templates, self.norms], as_of=as_of)['places'][0]

    def test_place_with_anchor_follows_only_that_anchor(self):
        self.assertEqual('action-needed', self.statuses('payout.cash', '2027-04-01')['status'])
        self.assertEqual('current', self.statuses('interest.free', '2027-04-01')['status'])

    def test_anchors_of_a_dependency_are_not_followed(self):
        wrapper = {'id': 'ru/pack', 'kind': 'template', 'version': '1.0.0', 'content_sha256': 'd' * 64,
                   'dependencies': [{'id': 'ru/loan', 'range': '^1.0.0'}]}
        self.templates['units'].append(wrapper)
        self.record['places'][0].update(unit='ru/pack', version='1.0.0', content_sha256='d' * 64)
        place = linkage.reconcile(self.record, [self.templates, self.norms], as_of='2027-04-01')['places'][0]
        self.assertEqual('current', place['status'])

    def test_edition_after_the_place_without_an_earlier_one(self):
        for u in self.norms['units']:
            if u['id'] == 'ru/gk/808':
                del u['history']
        self.assertEqual('action-needed', self.statuses('payout.cash', '2027-04-01')['status'])

    def test_repealed_norm_needs_action(self):
        for u in self.norms['units']:
            if u['id'] == 'ru/gk/814':
                u['edition']['effective_to'] = '2027-01-01'
        place = self.statuses('purpose.target', '2027-04-01')
        self.assertEqual('action-needed', place['status'])
        self.assertEqual('not in force since 2027-01-01', place['instruction'])


class CommandLine(unittest.TestCase):
    def test_validate_examples(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, linkage.main(['validate', *map(str, sorted(EX.rglob('*.json')))]))


if __name__ == '__main__':
    unittest.main()
