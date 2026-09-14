import copy
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import lifecycle as l


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'project'
        shutil.copytree(HERE/'examples/project',self.root)
        self.project=self.root/'project.json';self.plan=self.root/'update-plan.json';self.catalog=self.root/'release-catalog.json'
        self.old=self.root/'standards/docs.foundation.json'
    def save(self,path,data):path.write_text(l.c.dump(data))
    def compare(self,name):return l.comparison(self.old,self.root/'proposals'/name/'standard.json')
    def prepare(self,output=None):return l.prepare(self.project,self.plan,self.catalog,output=output)
    def snapshot(self):return {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_minor_and_major_obligations(self):
        self.assertEqual(self.compare('minor')['actualCategory'],'minor')
        self.assertIn('brief-intro',self.compare('minor')['requirements']['added'])
        major=self.compare('major')
        self.assertEqual(major['objectCompatibility'],'incompatible')
        self.assertEqual(major['readerCompatibility'],'compatible')
    def test_editorial_without_normative_change(self):
        d=l.c.load(self.old);d.update(version='1.0.1',title='Editorial title')
        p=self.root/'editorial.json';self.save(p,d)
        r=l.comparison(self.old,p)
        self.assertEqual(r['minimumStructuralCategory'],'patch')
        self.assertEqual(r['objectCompatibility'],'compatible')
    def test_normative_text_not_certified_by_author(self):
        d=l.c.load(self.old);d['version']='1.0.1';d['requirements'][1]['text']='Every link should be readable.'
        p=self.root/'text.json';self.save(p,d)
        self.assertEqual(l.comparison(self.old,p)['objectCompatibility'],'needs-review')
    def test_transition_claim_separate(self):
        r=l.comparison(self.old,self.root/'proposals/patch/standard.json',self.root/'proposals/patch/transition.json')
        self.assertEqual(r['authorAssessment']['objects'],'compatible')
        self.assertEqual(r['objectCompatibility'],'needs-review')
    def test_immutable_version(self):
        d=l.c.load(self.old);d['title']='Other'
        p=self.root/'bad.json';self.save(p,d)
        with self.assertRaisesRegex(ValueError,'immutable'):l.comparison(self.old,p)
    def test_new_major_obligation_with_patch_rejected(self):
        d=l.c.load(self.root/'proposals/major/standard.json');d['version']='1.0.1'
        p=self.root/'bad.json';self.save(p,d)
        self.assertFalse(l.comparison(self.old,p)['categorySufficient'])
    def test_impact_all_children_and_declaration(self):
        r=l.impact(self.project,'docs.foundation')
        self.assertTrue({'docs.api','docs.tutorial'}.issubset({x['id'] for x in r['affectedStandards']}))
        self.assertIn('docs/api/button.md',r['objects'])
        self.assertIn('docs/api/button.md.standards.json',r['declarations'])
        self.assertIn('external-consumers',r['coverage']['uninspected'])
    def test_usage_impact_not_inheritance(self):
        r=l.impact(self.project,'framework.utility')
        row=next(x for x in r['affectedStandards'] if x['id']=='framework.component')
        self.assertIn('uses',row['via'])
    def test_pins_stay_old_until_update(self):
        r=l.c.resolve(self.project,'docs/api/button.md')
        self.assertTrue(all(q['sourceVersion']=='1.0.0' for q in r['requirements']))
    def test_prepare_end_to_end_no_source_changes(self):
        before=self.snapshot();preview=self.prepare()
        dest=self.base/'updated';written=self.prepare(dest)
        self.assertEqual(preview,written);self.assertEqual(before,self.snapshot())
        r=l.c.resolve(dest/'project.json','docs/api/button.md')
        self.assertTrue(all(q['sourceVersion']=='1.0.1' for q in r['requirements']))
        self.assertEqual(r['declaration'],'consistent')
        self.assertFalse((dest/'docs/api/button.md').exists())
        self.assertFalse(written['newAdoptionReady'])
    def test_preparation_is_deterministic_and_exclusive(self):
        a=self.base/'a';b=self.base/'b';self.prepare(a);self.prepare(b)
        snap=lambda root:{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertEqual(snap(a),snap(b))
        with self.assertRaisesRegex(ValueError,'already-exists'):self.prepare(a)
    def test_missing_child_target_version(self):
        p=l.c.load(self.plan);p['changes']=[r for r in p['changes'] if r['source']['id']!='docs.api'];self.save(self.plan,p)
        with self.assertRaisesRegex(ValueError,'missing-target-version'):self.prepare()
    def test_catalog_collision(self):
        d=l.c.load(self.catalog);d['releases'].append(dict(id='docs.api',version='1.0.1',sha256='0'*64));self.save(self.catalog,d)
        with self.assertRaisesRegex(ValueError,'target-version-collision'):self.prepare()
    def test_changed_source_plan_pin(self):
        self.old.write_text(self.old.read_text()+' ')
        with self.assertRaises(ValueError):self.prepare()
    def test_declaration_conflict(self):
        p=self.root/'docs/api/button.md.standards.json';d=l.c.load(p);d['kind']='tutorial-page';self.save(p,d)
        with self.assertRaisesRegex(ValueError,'declaration-project-conflict'):self.prepare()
    def test_journal_states_and_order(self):
        ref=l.release(*l.standard(self.old));journal=self.root/'status.json'
        for state in ('draft','active','deprecated','withdrawn'):
            self.save(journal,dict(format='standard-contract-journal',formatVersion='lifecycle-draft-1',entries=[dict(sequence=1,release=ref,status=state,reason='Decision',decisionSource='Owner')]))
            r=l.journal_status(journal,[ref]);self.assertEqual(r['releases'][0]['status'],state)
            self.assertEqual(r['newAdoptionEligible'],state in ('active','deprecated'))
        self.assertEqual(l.journal_status(None,[ref])['releases'][0]['status'],'unknown')
        self.assertTrue(l.c.resolve(self.project,'docs/api/button.md')['requirements'])
    def test_evidence_current_then_object_stale(self):
        receipt=self.root/'receipt.json';self.save(receipt,l.evidence_snapshot(self.project,'docs/api/button.md','review','1.0.0'))
        check=lambda:l.evidence_check(self.project,'docs/api/button.md',receipt,'review','1.0.0')
        self.assertEqual(check()['applicability'],'current')
        (self.root/'docs/api/button.md').write_text('Changed')
        self.assertIn('objectSha256',check()['staleReasons'])
    def test_evidence_stale_rules_and_checker(self):
        receipt=self.root/'receipt.json';self.save(receipt,l.evidence_snapshot(self.project,'docs/api/button.md','review','1.0.0'))
        dest=self.base/'updated';self.prepare(dest)
        path=dest/'docs/api/button.md';path.write_bytes((self.root/'docs/api/button.md').read_bytes())
        r=l.evidence_check(dest/'project.json','docs/api/button.md',receipt,'review','1.0.1')
        self.assertIn('normativeSetSha256',r['staleReasons']);self.assertIn('checker',r['staleReasons'])
    def test_evidence_bytes_and_no_claim_certification(self):
        data=l.evidence_snapshot(self.project,'docs/api/button.md','review','1.0.0')
        proof=self.root/'proof.txt';proof.write_text('Reviewed')
        for row in data['results']:row.update(status='pass',evidence=[dict(path='proof.txt',sha256=l.digest(proof.read_bytes()))])
        receipt=self.root/'receipt.json';self.save(receipt,data)
        r=l.evidence_check(self.project,'docs/api/button.md',receipt,'review','1.0.0')
        self.assertEqual(r['recordedClaim'],'pass');self.assertFalse(r['claimVerified'])
        proof.write_text('Changed')
        self.assertIn('evidence-bytes',l.evidence_check(self.project,'docs/api/button.md',receipt,'review','1.0.0')['staleReasons'])
    def test_no_network(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')):
            self.prepare();l.impact(self.project,'docs.foundation')
    def test_source_changed_at_install(self):
        p=self.root/'tracked.txt';p.write_text('Changed')
        with self.assertRaisesRegex(ValueError,'source-changed'):l.install_tree({},None,{p:b'Old'})
    def test_migration_explicit_versions(self):
        source=self.base/'old';shutil.copytree(HERE.parent/'examples',source)
        project=source/'project.json';changes=[]
        for path in (source/'standards').glob('*.json'):
            changes.append(dict(source=dict(l.release(*l.standard(path)),path=path.relative_to(source).as_posix()),targetVersion='2.0.0'))
        plan=source/'plan.json';self.save(plan,dict(format='standard-contract-update-plan',formatVersion='lifecycle-draft-1',sourceProjectSha256=l.digest(project.read_bytes()),changes=changes))
        catalog=source/'catalog.json';self.save(catalog,dict(format='standard-contract-release-catalog',formatVersion='lifecycle-draft-1',releases=[]))
        dest=self.base/'migrated';r=l.migrate1(project,plan,catalog,dest)
        self.assertTrue(all(x['readerCompatibility']=='incompatible' for x in r['comparisons']))
        self.assertTrue(l.c.resolve(dest/'project.json','docs/api/page.md')['requirements'])
        d=l.c.load(plan);d['changes'].pop();self.save(plan,d)
        with self.assertRaisesRegex(ValueError,'missing-target-version'):l.migrate1(project,plan,catalog)

    def test_replacement_history(self):
        d=l.c.load(self.old);d['version']='2.0.0';d['requirements'][1]['id']='link-integrity'
        path=self.root/'renamed.json';self.save(path,d)
        t=dict(format='standard-contract-transition',formatVersion='lifecycle-draft-1',source=l.release(*l.standard(self.old)),target=l.release(*l.standard(path)),category='major',rationale='Renamed requirement',requiredChecks=['Review equivalence'],replacements=[{'from':'links','to':'link-integrity'}],assessment=dict(reader='compatible',objects='needs-review',decisionSource='Owner'))
        transition=self.root/'transition.json';self.save(transition,t)
        self.assertEqual(l.comparison(self.old,path,transition)['requirements']['replacements'],t['replacements'])
    def test_catalog_contradictory_identity(self):
        data=l.c.load(self.catalog);other=dict(data['releases'][0],sha256='0'*64);data['releases'].append(other);self.save(self.catalog,data)
        with self.assertRaisesRegex(ValueError,'immutable-release-conflict'):self.prepare()
    def test_journal_latest_decision_without_staling_technical_evidence(self):
        ref=l.release(*l.standard(self.old));journal=self.root/'journal-latest.json'
        self.save(journal,dict(format='standard-contract-journal',formatVersion='lifecycle-draft-1',entries=[dict(sequence=i,release=ref,status=state,reason='Decision',decisionSource='Owner') for i,state in [(1,'active'),(2,'withdrawn')]]))
        receipt=self.root/'receipt.json';self.save(receipt,l.evidence_snapshot(self.project,'docs/api/button.md','review','1.0.0'))
        r=l.evidence_check(self.project,'docs/api/button.md',receipt,'review','1.0.0',journal)
        self.assertEqual(r['applicability'],'current');self.assertFalse(r['lifecycle']['newAdoptionEligible'])
    def test_schemas_and_cli(self):
        from jsonschema import Draft202012Validator
        import subprocess
        for path in HERE.glob('*.schema.json'):Draft202012Validator.check_schema(l.c.load(path))
        r=subprocess.run([sys.executable,str(HERE/'lifecycle.py'),'impact',str(self.project),'docs.foundation'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertIn('objects',json.loads(r.stdout))
        r=subprocess.run([sys.executable,str(HERE/'lifecycle.py'),'prepare',str(self.project),str(self.plan),str(self.catalog)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertFalse(json.loads(r.stdout)['newAdoptionReady'])


if __name__=='__main__':unittest.main()
