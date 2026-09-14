import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('standard_contract', HERE / 'resolve.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        shutil.copytree(HERE / 'examples', self.root)
        self.project = self.root / 'project.json'

    def resolve(self, target='docs/api/button.json'):
        return m.resolve(self.project, target)

    def save(self, path, value):
        path.write_text(json.dumps(value, indent=2) + '\n')

    def test_inheritance_and_separate_sections(self):
        api = self.resolve()
        tutorial = self.resolve('docs/tutorials/start.md')
        self.assertEqual([s['id'] for s in api['standards']], ['docs.api', 'docs.foundation'])
        self.assertEqual([s['id'] for s in tutorial['standards']], ['docs.foundation', 'docs.tutorial'])
        self.assertEqual(len(api['requirements']), 4)

    def test_uses_does_not_inherit(self):
        result = self.resolve('src/components/button.json')
        self.assertEqual([s['id'] for s in result['standards']], ['framework.component'])

    def test_repeat_and_binding_order_do_not_change_output_or_sources(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        first = self.resolve()
        self.assertEqual(first, self.resolve())
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        config = m.load(self.project)
        config['bindings'].reverse()
        self.save(self.project, config)
        self.assertEqual(first, self.resolve())

    def test_changed_standard_is_rejected(self):
        with (self.root / 'standards/docs.foundation.json').open('a') as f:
            f.write(' ')
        with self.assertRaisesRegex(ValueError, 'Digest mismatch'):
            self.resolve()

    def test_no_binding_and_prefix_boundary(self):
        for target in ['other/file', 'docs/apix/file']:
            with self.assertRaisesRegex(ValueError, 'No binding'):
                self.resolve(target)

    def test_target_traversal_rejected(self):
        for target in ['../docs/api/file', '/docs/api/file', 'docs//api/file', 'docs/./api/file']:
            with self.assertRaises(ValueError):
                self.resolve(target)

    def test_manual_rules_never_automatically_pass(self):
        result = m.check(self.resolve(), m.load(self.root / 'api-page.json'))
        self.assertEqual(result['status'], 'needs-review')
        self.assertEqual(sum(r['status'] == 'pass' for r in result['requirements']), 2)
        bad = m.check(self.resolve(), {'language': 'en', 'layout': 'tutorial'})
        self.assertEqual(bad['status'], 'fail')

    def test_primitive_types_and_missing_null_are_distinct(self):
        rules = {'requirements': [{'key': 'x', 'level': 'must', 'verification': 'equals', 'property': 'x', 'value': True}]}
        self.assertEqual(m.check(rules, {'x': 1})['status'], 'fail')
        rules['requirements'][0]['value'] = None
        self.assertEqual(m.check(rules, {})['status'], 'fail')
        self.assertEqual(m.check(rules, {'x': None})['status'], 'pass')

    def add_rule(self, *, value='tutorial', sid='docs.other', kind='api-page'):
        standard = m.load(self.root / 'standards/docs.api.json')
        standard.update(id=sid, appliesTo=[kind], requirements=[dict(id='layout', level='must', text='Layout rule', verification='equals', property='layout', value=value)])
        standard.pop('extends')
        path = self.root / 'standards/other.json'
        self.save(path, standard)
        ref = dict(id=sid,version=standard['version'],path='standards/other.json',sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        config = m.load(self.project)
        config['bindings'][0]['standards'].append(ref)
        self.save(self.project, config)

    def test_conflicting_values_fail_without_last_writer_wins(self):
        self.add_rule()
        with self.assertRaisesRegex(ValueError, 'Conflicting mandatory values'):
            self.resolve()

    def test_same_identity_different_content_fails(self):
        self.add_rule(sid='docs.api')
        with self.assertRaisesRegex(ValueError, 'Conflicting versions or content'):
            self.resolve()

    def test_wrong_applicability_fails(self):
        self.add_rule(kind='component')
        with self.assertRaisesRegex(ValueError, 'does not apply'):
            self.resolve()

    def test_duplicate_json_keys_rejected(self):
        self.project.write_text('{"format": "a", "format": "b"}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            self.resolve()

    def test_symlink_cannot_escape_root(self):
        external = self.root.parent / 'external.json'
        shutil.copy(self.root / 'standards/docs.api.json', external)
        (self.root / 'standards/docs.api.json').unlink()
        (self.root / 'standards/docs.api.json').symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'leaves project root'):
            self.resolve()

    def test_unknown_semantics_rejected(self):
        standard = m.load(self.root / 'standards/docs.api.json')
        standard['requirements'][0]['verification'] = 'execute-command'
        from jsonschema.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            m.validate(standard, 'standard')

    def test_duplicate_binding_deduplicates_requirements(self):
        first = self.resolve()
        config = m.load(self.project)
        config['bindings'].append(copy.deepcopy(config['bindings'][0]))
        self.save(self.project, config)
        self.assertEqual(first, self.resolve())

    def test_all_published_examples_match_schema(self):
        for path in (self.root / 'standards').glob('*.json'):
            m.validate(m.load(path), 'standard')
        m.validate(m.load(self.project), 'project')

    def test_invalid_unselected_binding_is_not_silently_ignored(self):
        config = m.load(self.project)
        config['bindings'][1]['prefix'] = '../outside'
        self.save(self.project, config)
        with self.assertRaisesRegex(ValueError, 'normalized relative'):
            self.resolve()

    def test_artifact_check_does_not_mutate_input(self):
        artifact = m.load(self.root / 'api-page.json')
        original = copy.deepcopy(artifact)
        first = m.check(self.resolve(), artifact)
        self.assertEqual(first, m.check(self.resolve(), artifact))
        self.assertEqual(artifact, original)


if __name__ == '__main__':
    unittest.main()
