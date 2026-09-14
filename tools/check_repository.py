#!/usr/bin/env python3
"""Check local documentation links, language policy and public snapshot consistency."""
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote,urlsplit
from aifirst import ROOT,Reader

def main():
    errors=[]
    paths=[p for p in ROOT.rglob('*') if p.is_file() and not any(
        part in {'.git','.venv','__pycache__','source','output','archives','.simai','graph'} for part in p.relative_to(ROOT).parts)]
    for p in paths:
        if p.name in {'AGENTS.md','graph.json'}:continue
        if p.suffix not in ('.md','.json','.py','.yml','.txt'):continue
        text=p.read_text(encoding='utf-8')
        if re.search('[\u0400-\u04ff]',text):errors.append(str(p.relative_to(ROOT))+': non-English Cyrillic text')
        if '/'+'Users/' in text or '/'+'home/' in text:errors.append(str(p.relative_to(ROOT))+': host-local path')
        if p.suffix=='.md':
            # Fenced examples are illustrative, not repository navigation links.
            prose=re.sub(r'```.*?```','',text,flags=re.S)
            for link in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',prose):
                link=link.split()[0].strip('<>');url=urlsplit(link)
                if url.scheme or link.startswith('#'):continue
                if not (p.parent/unquote(url.path)).exists():errors.append(str(p.relative_to(ROOT))+': broken link '+link)
    result=subprocess.run([sys.executable,str(ROOT/'tools/build_manifest.py'),'--check'])
    if result.returncode:errors.append('Root manifest is stale')
    for target in [ROOT,*[ROOT/'examples'/n for n in ('minimal','catalog','service','collection')]]:
        try:
            r=Reader(target);r.discover();r.inventory();report=r.publication()
            if report['errors']:errors.append(str(target.relative_to(ROOT))+': '+json.dumps(report['errors']))
        except Exception as exc:errors.append(str(target.relative_to(ROOT))+': '+str(exc))
    if errors:
        print('\n'.join(errors));return 1
    print('PASS: documentation links, English source policy, root inventory and four example publications')
    return 0
if __name__=='__main__':raise SystemExit(main())
