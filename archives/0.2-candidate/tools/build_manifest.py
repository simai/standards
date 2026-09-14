#!/usr/bin/env python3
"""Build this repository's explicitly allowlisted public knowledge inventory."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# This is a reviewed public inventory, never a recursive filesystem export.
PAGES=[
 ('overview','README.md','AI First overview','Purpose, scope and initial adoption.'),
 ('core','spec/core.md','Core data model','Manifest, catalogs, items, scope and compatibility.'),
 ('discovery','spec/discovery.md','Discovery and reading','Locate descriptions and retrieve materials within bounded access.'),
 ('knowledge','profiles/knowledge.md','Knowledge profile','Ordinary materials, examples, languages and source attribution.'),
 ('capability','profiles/capability.md','Capability description profile','Describe existing operations without authorizing execution.'),
 ('security','spec/security.md','Security and trust','Untrusted content, network access and publisher boundaries.'),
 ('conformance','spec/conformance.md','Conformance and errors','Structure, publication and runtime evidence distinctions.'),
 ('quickstart','docs/quickstart.md','Project adoption quickstart','Add ai.json and validate a static or local publication.'),
 ('publisher','docs/publisher.md','Publisher guide','Build and update consistent public snapshots.'),
 ('reader','docs/reader.md','Reader guide','Use the reference CLI and integrate bounded retrieval.')]
def build():
    items=[]
    for key,path,title,description in PAGES:
        digest=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        items.append({'id':'urn:ai-first:specification:0.1:'+key,'kind':'knowledge',
          'title':title,'description':description,'language':'en','revision':digest,
          'status':'published','source':'./'+path,'appliesTo':{'product':'urn:ai-first:specification','versions':['0.1']},
          'representations':[{'href':'./'+path,'mediaType':'text/markdown','sha256':digest}]})
    snapshot=hashlib.sha256(json.dumps(items,sort_keys=True).encode()).hexdigest()
    return {'format':'ai-first','formatVersion':'0.1','document':'manifest',
      'revision':snapshot,'resource':{'id':'urn:ai-first:specification:0.1',
      'name':'AI First 0.1 Pilot Specification','description':'An open specification for discoverable resource knowledge and capability descriptions. No operation executor or international recognition is implied.',
      'language':'en','scope':'./','publisher':{'name':'AI First contributors'}},'items':items}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=json.dumps(build(),indent=2)+'\n';target=ROOT/'ai.json'
    if args.check:
        if not target.exists() or target.read_text()!=data:
            print('ai.json is stale: run python3 tools/build_manifest.py');return 1
        print('ai.json matches its allowlisted source documents');return 0
    target.write_text(data);print('Built ai.json from 10 public source documents');return 0
if __name__=='__main__':raise SystemExit(main())
