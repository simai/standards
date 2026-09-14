import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from test_10_core import manifest, item, catalog, link

ROOT = Path(__file__).resolve().parents[1]
NODE = os.environ.get('AI_FIRST_NODE') or shutil.which('node')


class Interop10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise unittest.SkipTest('Node >=20 required; set AI_FIRST_NODE')
        check = subprocess.run([NODE, '--version'], capture_output=True)
        if check.returncode:
            raise RuntimeError('Node runtime does not start; set AI_FIRST_NODE to a working Node >=20')

    def test_shared_corpus_python_javascript(self):
        cases = json.loads((ROOT/'conformance/1.0/shared-cases.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['name']), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); i = item(appliesTo={'product': 'urn:product', 'versions': ['1.0']})
                doc = manifest(items=[i]); args = []; mutation = case['mutation']
                text = '# Example\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n\n```js\nconsole.log(42);\n```\n'
                (root/'guide.md').write_text(text)
                if mutation in ('catalog','pin'):
                    doc.pop('items'); doc['catalogs'] = [link(revision='wrong' if mutation=='pin' else 'child-1')]
                    (root/'child.json').write_text(json.dumps(catalog([i])))
                    if mutation=='pin':doc['items']=[item(9)]
                if mutation in ('missing','selective','missing-profile'):
                    doc['catalogs'] = [link(select={'languages': ['fr']})] if mutation!='missing' else [link()]
                    if mutation=='selective':doc['requires']=['selective-catalogs']
                    args=['--language','en']
                if mutation=='digest':i['representations'][0]['sha256']='0'*64
                if mutation=='version':doc['formatVersion']='9.9'
                if mutation=='language':args=['--language','fr']
                if mutation=='exact-version':args=['--version','1']
                if mutation=='duplicate-id':doc['items'].append(copy.deepcopy(i))
                raw=json.dumps(doc)
                if mutation=='duplicate':raw=raw.replace('"format":', '"format":"duplicate", "format":',1)
                (root/'ai.json').write_text(raw)
                py=subprocess.run([sys.executable,str(ROOT/'tools/aifirst10.py'),'read',str(root),*args],capture_output=True,text=True)
                js=subprocess.run([NODE,str(ROOT/'tools/aifirst10.mjs'),'read',str(root),*args],capture_output=True,text=True)
                self.assertEqual(py.returncode,js.returncode,(py.stdout,js.stdout,js.stderr))
                left=json.loads(py.stdout);right=json.loads(js.stdout)
                if 'error' in left:
                    self.assertEqual(left['error']['code'],right['error']['code'])
                    self.assertEqual(left['error']['code'],case['expected'])
                else:
                    for key in ('id','revision','publicationRevision','source','representation','mediaType','sha256','text','language','completeness','omittedCatalogs'):
                        self.assertEqual(left[key],right[key],key)
                    self.assertEqual([e['code'] for e in left['errors']],[e['code'] for e in right['errors']])
                    self.assertEqual(left['completeness'], 'complete' if case['expected']=='pass' else case['expected'])
                    self.assertEqual(left['text'],text)

    def test_javascript_strict_json_and_discovery_parser(self):
        script = r'''
import {strictJSON, declarations} from './tools/aifirst10.mjs';
import assert from 'node:assert/strict';
for(const text of ['{"x":1,"x":2}', '\ufeff{}', '{"x":"\\ud800"}', '[1,]', '1e999', 'true false']) {
  assert.throws(()=>strictJSON(Buffer.from(text)), e=>e.code==='invalid-json');
}
const header='<a.json>; rel="describedby"; type="application/json"; title="a,b"; ai-first="1.0"';
assert.deepEqual(declarations('',header),['a.json']);
assert.deepEqual(declarations('<link rel="describedby" type="application/json" data-ai-first="1.0" href="a.json">'),['a.json']);
'''
        result=subprocess.run([NODE,'--input-type=module','-e',script],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()

