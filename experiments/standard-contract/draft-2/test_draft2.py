import copy
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract as c
import migrate as migration


class Draft2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'project'
        shutil.copytree(HERE / 'examples/project', self.root)
        self.project = self.root / 'project.json'

    def save(self, path, value):
        path.write_text(c.dump(value))

    def resolve(self, target='docs/api/button.md'):
        return c.resolve(self.project, target)

    def repin_api(self, change):
        path = self.root / 'standards/docs.api.json'
        doc = c.load(path); change(doc); self.save(path, doc)
        config = c.load(self.project)
        config['bindings'][0]['standards'][0]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.save(self.project, config)
        (self.root / 'docs/api/button.md.standards.json').unlink(missing_ok=True)

    def test_sections_and_usage_are_distinct(self):
        api = self.resolve()
        self.assertEqual(api['declaration'], 'consistent')
        self.assertEqual(len(api['requirements']), 4)
        tutorial = self.resolve('docs/tutorials/start.md')
        self.assertTrue(any(r['source'] == 'docs.tutorial' for r in tutorial['requirements']))
        component = self.resolve('src/components/button.json')
        self.assertEqual({r['source'] for r in component['requirements']}, {'framework.component'})
        self.assertTrue(any(e['relation'] == 'uses' and e['availability'] == 'verified-bytes' for e in component['relations']))

    def test_no_network_and_repeatability(self):
        snapshot = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
            first = self.resolve()
            self.assertEqual(first, self.resolve())
        self.assertEqual(snapshot, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual(first['artifactConformance'], 'not-assessed')

    def test_bundle_relocation(self):
        first = self.resolve()
        moved = self.base / 'moved'; shutil.copytree(self.root, moved)
        self.assertEqual(first, c.resolve(moved/'project.json', 'docs/api/button.md'))

    def test_portable_standalone(self):
        path = HERE/'examples/portable/button.md.standards.json'
        first = c.standalone(path)
        moved = self.base/'portable';shutil.copytree(path.parent,moved)
        self.assertEqual(first,c.standalone(moved/path.name))

    def test_declaration_conflict(self):
        path = self.root/'docs/api/button.md.standards.json'
        data=c.load(path);data['kind']='tutorial-page';self.save(path,data)
        with self.assertRaisesRegex(ValueError,'declaration-project-conflict'):self.resolve()

    def test_declaration_own_path_is_verified(self):
        path = self.root/'docs/api/button.md.standards.json'
        data=c.load(path);data['standards'][0]['path']='missing.json';self.save(path,data)
        with self.assertRaises(OSError):self.resolve()

    def test_wrong_declaration_target(self):
        path = self.root/'docs/api/button.md.standards.json'
        data=c.load(path);data['target']='other.md';self.save(path,data)
        with self.assertRaisesRegex(ValueError,'target-mismatch'):self.resolve()

    def test_declare_preview_create_refuse_overwrite(self):
        target='docs/tutorials/start.md';out=self.root/(target+'.standards.json')
        preview=c.prepare(self.project,target)
        self.assertFalse(out.exists())
        created=c.prepare(self.project,target,True)
        self.assertEqual(preview['declaration'],created['declaration'])
        self.assertEqual(c.resolve(self.project,target)['declaration'],'consistent')
        with self.assertRaises(FileExistsError):c.prepare(self.project,target,True)

    def test_modified_pin(self):
        with (self.root/'standards/docs.foundation.json').open('a') as stream:stream.write(' ')
        with self.assertRaisesRegex(ValueError,'digest-mismatch'):self.resolve()

    def test_wrong_identity(self):
        self.repin_api(lambda d:d.update(version='9.0.0'))
        with self.assertRaisesRegex(ValueError,'identity-version-mismatch'):self.resolve()

    def test_missing_inherited_standard(self):
        (self.root/'standards/docs.foundation.json').unlink()
        with self.assertRaises(FileNotFoundError):self.resolve()

    def test_url_only_usage_blocks_context_not_resolution(self):
        self.repin_api(lambda d:d.update(uses=[dict(id='external.api',version='1.0.0',url='https://example.org/api',description='Required contract')]))
        result=self.resolve();self.assertEqual(result['normativeContext'],'incomplete')
        self.assertEqual(c.check(result,{'language':'en','layout':'reference'})['status'],'needs-review')

    def test_addressless_usage_is_explicit(self):
        self.repin_api(lambda d:d.update(uses=[dict(id='external.api',version='1.0.0',description='Location unknown')]))
        self.assertTrue(any(e['availability']=='missing-location' for e in self.resolve()['relations']))

    def test_informative_missing_file_does_not_block_context(self):
        self.repin_api(lambda d:d.update(references=[dict(id='notes',version='1.0.0',path='absent.md',sha256='0'*64)]))
        result=self.resolve();self.assertEqual(result['normativeContext'],'available')
        self.assertTrue(any(e['availability']=='missing' for e in result['relations']))

    def test_missing_local_usage_fails(self):
        self.repin_api(lambda d:d.update(uses=[dict(id='notes',version='1.0.0',path='absent.md',sha256='0'*64,description='Required')]))
        with self.assertRaisesRegex(ValueError,'missing-local-dependency'):self.resolve()

    def test_root_escape_even_for_informative_link(self):
        self.repin_api(lambda d:d.update(references=[dict(id='notes',version='1.0.0',path='../../outside',sha256='0'*64)]))
        with self.assertRaisesRegex(ValueError,'path-outside-bundle'):self.resolve()

    def test_symlink_escape(self):
        external=self.base/'outside';external.write_text('outside')
        path=self.root/'standards/format.md';path.unlink();path.symlink_to(external)
        with self.assertRaisesRegex(ValueError,'path-outside-bundle'):self.resolve()

    def test_artifact_claims_remain_separate(self):
        resolved=self.resolve()
        self.assertEqual(c.check(resolved,{'language':'en','layout':'reference'})['status'],'needs-review')
        self.assertEqual(c.check(resolved,{'language':'en','layout':'tutorial'})['status'],'fail')
        small=copy.deepcopy(resolved);small['requirements']=[r for r in small['requirements'] if r['verification']=='equals']
        self.assertEqual(c.check(small,{'language':'en','layout':'reference'})['status'],'pass')
        small['normativeContext']='incomplete'
        self.assertEqual(c.check(small,{'language':'en','layout':'reference'})['status'],'needs-review')

    def test_old_version_not_reinterpreted(self):
        from jsonschema import ValidationError
        data=c.load(self.project);data['formatVersion']='draft-1';self.save(self.project,data)
        with self.assertRaises(ValidationError):self.resolve()

    def test_migration_preview_write_repin_and_preserve(self):
        source=self.base/'old';shutil.copytree(HERE.parent/'examples',source)
        before={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
        report=migration.migrate(source/'project.json')
        self.assertEqual(len(report['missingInformation']),1)
        dest=self.base/'converted'
        self.assertEqual(report,migration.migrate(source/'project.json',dest))
        result=c.resolve(dest/'project.json','docs/api/button.md')
        self.assertTrue(all(r['sourceVersion']=='1.0.1' for r in result['requirements']))
        self.assertEqual(c.resolve(dest/'project.json','src/components/button.json')['normativeContext'],'incomplete')
        self.assertEqual(before,{p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()})
        with self.assertRaisesRegex(ValueError,'already-exists'):migration.migrate(source/'project.json',dest)

    def test_migration_failure_does_not_create_destination(self):
        source=self.base/'old';shutil.copytree(HERE.parent/'examples',source)
        (source/'standards/docs.foundation.json').write_text('{}')
        dest=self.base/'converted'
        with self.assertRaises(ValueError):migration.migrate(source/'project.json',dest)
        self.assertFalse(dest.exists())

    def test_conflicting_values_fail(self):
        def change(d):
            d['requirements'].append(dict(id='wrong-language',level='must',text='Use another language',verification='equals',property='language',value='fr'))
        self.repin_api(change)
        with self.assertRaisesRegex(ValueError,'conflicting-mandatory-values'):self.resolve()

    def test_informative_changed_digest_is_reported(self):
        self.repin_api(lambda d:d.update(references=[dict(id='notes',version='1.0.0',path='format.md',sha256='0'*64)]))
        result=self.resolve()
        self.assertEqual(result['normativeContext'],'available')
        self.assertTrue(any(e['availability']=='digest-mismatch' for e in result['relations']))

    def test_standalone_cannot_reach_project_parent(self):
        with self.assertRaisesRegex(ValueError,'path-outside-bundle'):
            c.standalone(self.root/'docs/api/button.md.standards.json')

    def test_local_examples_and_schema_contracts(self):
        from jsonschema import Draft202012Validator
        for path in HERE.glob('*.schema.json'):Draft202012Validator.check_schema(c.load(path))
        for path in (HERE/'examples').rglob('*.json'):
            data=c.load(path)
            name={'standard-contract':'standard','standard-contract-project':'project','standard-contract-declaration':'declaration'}.get(data.get('format'))
            if name:c.validate(data,name)
        for path in (HERE/'examples').rglob('format.md'):
            self.assertEqual(path.read_bytes(),(HERE/'SPEC.md').read_bytes())

    def test_cli_exit_codes(self):
        import subprocess
        args=[sys.executable,str(HERE/'contract.py'),'resolve',str(self.project),'docs/api/button.md']
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)['artifactConformance'],'not-assessed')
        result=subprocess.run(args+['--artifact',str(self.root/'api-projection.json')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)['status'],'needs-review')
        result=subprocess.run([sys.executable,str(HERE/'contract.py'),'resolve',str(self.project),'unknown/file'],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(json.loads(result.stdout)['status'],'error')


if __name__=='__main__':unittest.main()
