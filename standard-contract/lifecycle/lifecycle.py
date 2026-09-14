#!/usr/bin/env python3
"""Stable local lifecycle profile 1.0.0. Read-only unless --output is supplied."""
import argparse
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
from jsonschema import Draft202012Validator, ValidationError

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '1.0'))
import contract as c

EXCLUDED = {'.git', '.venv', 'node_modules', '__pycache__', 'output', 'build', 'dist'}


def digest(raw): return hashlib.sha256(raw).hexdigest()
def fingerprint(value): return digest(c.dump(value).encode())
def release(doc, raw): return {'id': doc['id'], 'version': doc['version'], 'sha256': digest(raw)}
def key(ref): return (ref['id'], ref['version'], ref['sha256'])
def version(value): return tuple(int(x) for x in value.split('.'))


def validate(data, name):
    Draft202012Validator(c.load(HERE / (name + '.schema.json'))).validate(data)
    if name in ('catalog','journal'):
        refs=data['releases'] if name=='catalog' else [r['release'] for r in data['entries']]
        seen={}
        for ref in refs:
            identity=(ref['id'],ref['version'])
            if identity in seen and seen[identity]!=ref['sha256']:raise ValueError('immutable-release-conflict')
            seen[identity]=ref['sha256']
    return data


def standard(path):
    raw = c.raw_read(path); data = c.decode(raw)
    if data.get('formatVersion') == 'draft-1':
        schema = c.load(HERE.parent / 'standard.schema.json')
        Draft202012Validator(schema).validate(data)
    else:
        c.validate(data, 'standard')
    ids = [r['id'] for r in data['requirements']]
    if len(set(ids)) != len(ids): raise ValueError('duplicate-requirement')
    return data, raw


def comparison(old, new, transition=None):
    a, ar = standard(old); b, br = standard(new)
    if a['id'] != b['id']: raise ValueError('different-standard-identities')
    source, target = release(a, ar), release(b, br)
    if source['version'] == target['version'] and source['sha256'] != target['sha256']:
        raise ValueError('immutable-release-rewritten')
    if version(b['version']) < version(a['version']): raise ValueError('version-regression')
    left = {r['id']: r for r in a['requirements']}; right = {r['id']: r for r in b['requirements']}
    added = sorted(right.keys() - left.keys()); removed = sorted(left.keys() - right.keys())
    changed = sorted(k for k in left.keys() & right.keys() if left[k] != right[k])
    reader = 'compatible' if a['formatVersion'] == b['formatVersion'] else 'incompatible'
    objects, minimum = 'compatible', 'patch'
    reasons = []
    def review(reason):
        nonlocal objects
        if objects != 'incompatible': objects = 'needs-review'
        reasons.append(reason)
    def breaking(reason):
        nonlocal objects, minimum
        objects, minimum = 'incompatible', 'major'; reasons.append(reason)
    for rid in added:
        if right[rid]['level'] == 'must': breaking('new-mandatory-requirement:' + rid)
        elif minimum != 'major': minimum = 'minor'
    for rid in removed:
        # Removal may relax object acceptance but changes the promised standard.
        if left[rid]['level'] == 'must':
            minimum = 'major'; review('removed-mandatory-guarantee:' + rid)
        elif minimum == 'patch': minimum = 'minor'
    for rid in changed:
        x,y=left[rid],right[rid]
        if x['level'] != 'must' and y['level'] == 'must': breaking('strengthened-level:' + rid)
        elif x['level'] == 'must' and y['level'] != 'must':
            minimum='major'; review('removed-mandatory-guarantee:' + rid)
        if x['text'] != y['text']: review('normative-text-changed:' + rid)
        if any(x.get(k) != y.get(k) for k in ('verification','property','value')):
            if x['verification'] == y['verification'] == 'equals' and y['level'] == 'must': breaking('mandatory-constraint-changed:' + rid)
            else: review('verification-changed:' + rid)
    if set(a['appliesTo']) - set(b['appliesTo']): breaking('applicability-narrowed')
    elif set(b['appliesTo']) - set(a['appliesTo']) and minimum == 'patch': minimum='minor'
    dependencies = [r for r in ('extends','uses','specification') if a.get(r) != b.get(r)]
    if dependencies: review('normative-dependencies-changed')
    if reader == 'incompatible': minimum='major'; reasons.append('old-reader-cannot-read-target-envelope')
    if 'extensions' in a or 'extensions' in b:
        if a.get('extensions') != b.get('extensions'): review('extension-metadata-changed')
    before,after=version(a['version']),version(b['version'])
    actual='major' if after[0]>before[0] else ('minor' if after[1]>before[1] else ('patch' if after[2]>before[2] else 'none'))
    ranks={'none':0,'patch':1,'minor':2,'major':3}
    sufficient = source==target or ranks[actual]>=ranks[minimum]
    result={'format':'standard-contract-comparison','formatVersion':'1.0','source':source,'target':target,
            'requirements':{'added':added,'removed':removed,'changed':changed,'replacements':[]},
            'dependencyChanges':dependencies,'readerCompatibility':reader,'objectCompatibility':objects,
            'minimumStructuralCategory':minimum,'actualCategory':actual,'categorySufficient':sufficient,
            'questions':sorted(set(reasons)),'authorAssessment':None,'semanticAssessment':'not-inferred-from-author-claim'}
    if transition:
        t=validate(c.load(transition),'transition')
        if t['source']!=source or t['target']!=target: raise ValueError('transition-release-mismatch')
        if t['category']!=actual: raise ValueError('transition-category-mismatch')
        if len({r['from'] for r in t['replacements']})!=len(t['replacements']) or len({r['to'] for r in t['replacements']})!=len(t['replacements']):raise ValueError('ambiguous-requirement-replacement')
        for row in t['replacements']:
            if row['from'] not in removed or row['to'] not in added: raise ValueError('invalid-requirement-replacement')
        result['requirements']['replacements']=sorted(t['replacements'],key=c.dump)
        result['authorAssessment']=t['assessment']
        result['requiredChecks']=t['requiredChecks']
    return result


def inventory(project):
    project=Path(project).resolve();root=project.parent
    config=c.load(project);c.validate(config,'project')
    standards, ignored, objects, declarations = {}, [], [], []
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent=Path(directory)
        for name in list(dirs):
            path=parent/name
            if name in EXCLUDED or path.is_symlink():
                ignored.append(path.relative_to(root).as_posix());dirs.remove(name)
        for name in files:
            path=parent/name;rel=path.relative_to(root).as_posix()
            if path.is_symlink():
                ignored.append(rel);continue
            if path.suffix=='.json':
                try: data=c.load(path)
                except (ValueError,OSError):
                    ignored.append(rel);continue
                if isinstance(data,dict) and data.get('format')=='standard-contract':
                    doc,raw=standard(path)
                    if doc['formatVersion']!='1.0':
                        ignored.append(rel);continue
                    standards[path]=(doc,raw);continue
                if name.endswith('.standards.json'):
                    c.validate(data,'declaration');declarations.append(rel);continue
            if any(rel==b['prefix'] or rel.startswith(b['prefix']+'/') for b in config['bindings']):
                objects.append(rel)
    for b in config['bindings']:c.resolve(project,b['prefix'])
    for obj in sorted(objects):c.resolve(project,obj)
    for declaration in declarations:
        target=declaration[:-len('.standards.json')]
        if any(target==b['prefix'] or target.startswith(b['prefix']+'/') for b in config['bindings']):c.resolve(project,target)
    edges=[]
    for path,(doc,raw) in standards.items():
        for relation in ('extends','uses'):
            for ref in doc.get(relation,[]):
                if 'path' in ref:
                    dest,_=c.verify_ref(root,path.parent,ref)
                    if dest in standards:
                        other=standards[dest][0]
                        if (other['id'],other['version'])!=(ref['id'],ref['version']):raise ValueError('dependency-identity-mismatch')
                    edges.append((path,relation,ref,dest))
                else:edges.append((path,relation,ref,None))
    return root,config,standards,edges,sorted(objects),sorted(declarations),sorted(ignored)


def impact(project, sid):
    root,config,standards,edges,objects,declarations,ignored=inventory(project)
    affected={path:{'selected-standard'} for path,(d,_) in standards.items() if d['id']==sid}
    # A referenced opaque contract can have consumers without a standard envelope.
    for path,rel,ref,dest in edges:
        if ref['id']==sid:affected.setdefault(path,set()).add(rel)
    changed=True
    while changed:
        changed=False
        for path,rel,ref,dest in edges:
            if dest in affected and path not in affected:
                affected[path]={rel};changed=True
            elif dest in affected:affected.setdefault(path,set()).add(rel)
    bindings=[]
    for b in config['bindings']:
        selected=[c.confined(root,root,r['path']) for r in b['standards']]
        if any(p in affected for p in selected):bindings.append(b['prefix'])
    hit=lambda target:any(target==p or target.startswith(p+'/') for p in bindings)
    return {'format':'standard-contract-impact','formatVersion':'1.0','standardId':sid,
            'affectedStandards':[dict(path=p.relative_to(root).as_posix(),id=standards[p][0]['id'],via=sorted(affected[p])) for p in sorted(affected)],
            'affectedBindings':sorted(set(bindings)),'objects':[p for p in objects if hit(p)],
            'declarations':[p for p in declarations if hit(p[:-len('.standards.json')])],
            'coverage':{'root':'project-configuration-directory','checkedPrefixes':sorted(b['prefix'] for b in config['bindings']),
                        'excludedPaths':ignored,'uninspected':['external-consumers','future-objects','nonlocal-contract-internals','content-outside-bound-prefixes']}}


def journal_status(journal, refs):
    records={};sequences=set()
    if journal:
        data=validate(c.load(journal),'journal')
        previous=0
        for row in data['entries']:
            if row['sequence']<=previous or row['sequence'] in sequences:raise ValueError('journal-sequence-order')
            previous=row['sequence'];sequences.add(previous);records[key(row['release'])]=row
    results=[]
    for ref in sorted(refs,key=c.dump):
        row=records.get(key(ref));state=row['status'] if row else 'unknown'
        results.append({'release':ref,'status':state,'reason':row['reason'] if row else 'no-local-decision',
                        'decisionSource':row['decisionSource'] if row else None})
    return {'releases':results,'warnings':[r for r in results if r['status']=='deprecated'],
            'newAdoptionEligible':all(r['status'] in ('active','deprecated') for r in results),
            'authenticity':'not-established','scope':'supplied-local-journal'}


def normative_set(resolution):
    # Addresses do not change meaning when identical pinned inputs are relocated.
    refs={key(e['to']):{k:e['to'][k] for k in ('id','version','sha256') if k in e['to']}
          for e in resolution['relations'] if e['relation']!='references' and 'sha256' in e['to']}
    missing=[e for e in resolution['relations'] if e['relation']!='references' and e['availability']!='verified-bytes']
    return fingerprint({'formatVersion':resolution['formatVersion'],'kind':resolution['kind'],
                        'requirements':resolution['requirements'],'pins':[refs[k] for k in sorted(refs)],'missing':missing})


def evidence_snapshot(project,target,checker_id,checker_version):
    r=c.resolve(project,target);root=Path(project).resolve().parent
    path=c.confined(root,root,target)
    data={'format':'standard-contract-evidence','formatVersion':'1.0',
          'objectSha256':digest(c.raw_read(path)),'normativeSetSha256':normative_set(r),
          'checker':{'id':checker_id,'version':checker_version},
          'results':[{'requirement':q['key'],'status':'not-checked','evidence':[]} for q in r['requirements']]}
    validate(data,'evidence');return data


def evidence_check(project,target,receipt,checker_id,checker_version,journal=None):
    current=evidence_snapshot(project,target,checker_id,checker_version)
    receipt=Path(receipt).resolve();data=validate(c.load(receipt),'evidence')
    stale=[field for field in ('objectSha256','normativeSetSha256','checker') if data[field]!=current[field]]
    expected={r['requirement'] for r in current['results']};actual=[r['requirement'] for r in data['results']]
    if set(actual)!=expected or len(actual)!=len(set(actual)):stale.append('requirement-coverage')
    for row in data['results']:
        for evidence in row['evidence']:
            path=c.confined(receipt.parent,receipt.parent,evidence['path'])
            if digest(c.raw_read(path))!=evidence['sha256']:stale.append('evidence-bytes')
    r=c.resolve(project,target)
    mandatory={q['key'] for q in r['requirements'] if q['level']=='must'}
    claims=[q for q in data['results'] if q['requirement'] in mandatory]
    claim='fail' if any(q['status']=='fail' for q in claims) else ('not-checked' if any(q['status']=='not-checked' for q in claims) else 'pass')
    refs={key(e['to']):{k:e['to'][k] for k in ('id','version','sha256')} for e in r['relations'] if e['relation'] in ('selected','extends')}
    return {'applicability':'stale' if stale else 'current','staleReasons':sorted(set(stale)),
            'recordedClaim':claim,'claimVerified':False,'normativeContext':r['normativeContext'],
            'lifecycle':journal_status(journal,list(refs.values())),
            'meaning':'Current bindings and intact files do not certify evidence semantics or authority.'}


def install_tree(files, destination, snapshots):
    for path,raw in snapshots.items():
        if c.raw_read(path)!=raw:raise ValueError('source-changed-during-preparation')
    if destination is None:return
    dest=Path(destination).absolute()
    if dest.exists() or dest.is_symlink():raise ValueError('destination-already-exists')
    if not dest.parent.is_dir():raise ValueError('destination-parent-missing')
    stage=Path(tempfile.mkdtemp(prefix='.lifecycle-',dir=dest.parent))
    try:
        for name,raw in sorted(files.items()):
            path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        projects=[]
        for n in files:
            if not n.endswith('.json'):continue
            try: parsed=c.decode(files[n])
            except ValueError:continue
            if isinstance(parsed,dict) and parsed.get('format')=='standard-contract-project':projects.append(n)
        for name in projects:
            data=c.load(stage/name)
            for binding in data['bindings']:c.resolve(stage/name,binding['prefix'])
            for side in stage.rglob('*.standards.json'):
                target=side.relative_to(stage).as_posix()[:-len('.standards.json')]
                c.resolve(stage/name,target)
        for path,raw in snapshots.items():
            if c.raw_read(path)!=raw:raise ValueError('source-changed-during-preparation')
        dest.mkdir()
        try:
            for child in stage.iterdir():shutil.move(str(child),str(dest/child.name))
        except Exception:
            shutil.rmtree(dest);raise
    finally:shutil.rmtree(stage)


def prepare(project,plan_file,catalog_file,journal=None,output=None):
    project=Path(project).resolve();root,config,standards,edges,objects,declarations,ignored=inventory(project)
    plan_file=Path(plan_file).resolve();catalog_file=Path(catalog_file).resolve()
    plan=validate(c.load(plan_file),'plan');catalog=validate(c.load(catalog_file),'catalog')
    snapshots={p:raw for p,(_,raw) in standards.items()}
    for p in (project,plan_file,catalog_file):snapshots[p]=c.raw_read(p)
    if journal:snapshots[Path(journal).resolve()]=c.raw_read(journal)
    if plan['sourceProjectSha256']!=digest(snapshots[project]):raise ValueError('source-project-mismatch')
    if output and Path(output).resolve().is_relative_to(root):raise ValueError('destination-inside-source')
    changes={}
    for row in plan['changes']:
        src=row['source'];path=c.confined(root,root,src['path'])
        if path in changes:raise ValueError('duplicate-update-entry')
        if path not in standards or release(*standards[path])!={k:src[k] for k in ('id','version','sha256')}:raise ValueError('source-standard-mismatch')
        if version(row['targetVersion'])<=version(src['version']):raise ValueError('target-version-must-increase')
        changes[path]=row
    files={};done={};active=set();used=set();comparisons=[];normative=[]
    def put(name,raw):
        if name in files and files[name]!=raw:raise ValueError('output-path-collision')
        files[name]=raw
    def read(path):
        raw=c.raw_read(path)
        if path in snapshots and snapshots[path]!=raw:raise ValueError('source-changed-during-preparation')
        snapshots[path]=raw;return raw
    def compile_standard(path):
        if path in active:raise ValueError('dependency-cycle')
        if path in done:return dict(done[path])
        if len(active)>64 or len(done)>256:raise ValueError('dependency-limit')
        active.add(path)
        original,raw=standards[path]
        row=changes.get(path);base=path.parent;doc=copy.deepcopy(original)
        if row:
            used.add(path)
            if 'replacement' in row:
                candidate=c.confined(root,plan_file.parent,row['replacement']['path'])
                candidate_raw=read(candidate)
                if digest(candidate_raw)!=row['replacement']['sha256']:raise ValueError('replacement-digest-mismatch')
                doc=c.decode(candidate_raw);c.validate(doc,'standard');base=candidate.parent
                if doc['id']!=original['id'] or doc['version']!=row['targetVersion']:raise ValueError('replacement-identity-version-mismatch')
            doc['version']=row['targetVersion']
        name=path.relative_to(root).as_posix()
        for rel in ('extends','uses','references','specification'):
            links=[doc[rel]] if rel=='specification' and rel in doc else doc.get(rel,[]) if rel!='specification' else []
            for ref in links:
                if 'path' not in ref:continue
                target=c.confined(root,base,ref['path'])
                try:content=read(target)
                except FileNotFoundError:
                    if rel=='references':
                        # A nonexistent informative reference stays explicitly missing.
                        ref['path']=Path(os.path.relpath(target,path.parent)).as_posix();continue
                    raise
                if digest(content)!=ref['sha256']:raise ValueError('dependency-digest-mismatch')
                if rel in ('extends','uses') and target in standards:
                    if (standards[target][0]['id'],standards[target][0]['version'])!=(ref['id'],ref['version']):raise ValueError('dependency-identity-mismatch')
                    pin=compile_standard(target)
                    ref.update({k:pin[k] for k in ('id','version','sha256')})
                    output_path=pin['path']
                else:
                    output_path=('_lifecycle_materials/'+digest(content)+'/'+target.name) if target in standards else target.relative_to(root).as_posix()
                    put(output_path,content)
                ref['path']=Path(os.path.relpath(root/output_path,path.parent)).as_posix()
        c.validate(doc,'standard')
        # Relocating support files changes serialized links and requires a version.
        changed=doc!=original
        if changed and not row:raise ValueError('missing-target-version: '+original['id'])
        content=c.dump(doc).encode() if changed else raw
        if digest(content)!=digest(raw) and not row:raise ValueError('missing-target-version: '+original['id'])
        put(name,content)
        pin=dict(release(doc,content),path=name);done[path]=pin;active.remove(path)
        if row:
            # Compare exact staged bytes using a temporary read surface.
            with tempfile.TemporaryDirectory() as tmp:
                before=Path(tmp)/'old.json';after=Path(tmp)/'new.json'
                before.write_bytes(raw);after.write_bytes(content)
                comparisons.append(comparison(before,after))
        normative.append({k:pin[k] for k in ('id','version','sha256')})
        return dict(pin)
    updated=copy.deepcopy(config)
    for binding in updated['bindings']:
        new=[]
        for ref in binding['standards']:
            source=c.confined(root,root,ref['path'])
            if source not in standards:raise ValueError('selected-standard-unavailable')
            if release(*standards[source])!={k:ref[k] for k in ('id','version','sha256')}:raise ValueError('binding-pin-mismatch')
            pin=compile_standard(source)
            new.append(dict(ref,**pin))
        binding['standards']=new
    if set(changes)!=used:raise ValueError('update-entry-not-reachable')
    local_releases=catalog['releases']+[release(*standards[path]) for path in done]
    for pin in normative:
        for known in local_releases:
            if (known['id'],known['version'])==(pin['id'],pin['version']) and known['sha256']!=pin['sha256']:raise ValueError('target-version-collision')
    if any(not r['categorySufficient'] for r in comparisons):raise ValueError('insufficient-target-version-category')
    project_name=project.name;put(project_name,c.dump(updated).encode())
    for declaration in declarations:
        target=declaration[:-len('.standards.json')]
        rows=[b for b in updated['bindings'] if target==b['prefix'] or target.startswith(b['prefix']+'/')]
        if not rows:continue
        path=root/declaration;snapshots[path]=read(path)
        previous=c.load(path);refs={key(r):dict(r) for b in rows for r in b['standards']}
        for ref in refs.values():ref['path']=Path(os.path.relpath(root/ref['path'],path.parent)).as_posix()
        new=dict(previous,standards=[refs[k] for k in sorted(refs)])
        put(declaration,c.dump(new).encode())
    status=journal_status(journal,normative)
    report={'format':'standard-contract-preparation','formatVersion':'1.0',
            'status':'candidate-requires-review','newAdoptionReady':False,
            'comparisons':sorted(comparisons,key=c.dump),'lifecycle':status,
            'files':[{'path':n,'sha256':digest(raw)} for n,raw in sorted(files.items())],
            'sourceProjectSha256':plan['sourceProjectSha256'],'objectsCopied':False,
            'pending':['object-domain-checks','owner-acceptance'],
            'collisionScope':'supplied-local-catalog-and-inspected-project','excludedPaths':ignored}
    put('lifecycle-report.json',c.dump(report).encode())
    # Validate even previews; temporary output is not a project mutation.
    with tempfile.TemporaryDirectory() as temp:
        trial=Path(temp)/'candidate';install_tree(files,trial,snapshots)
    install_tree(files,output,snapshots)
    return report


def migrate1(project,plan_file,catalog_file,output=None):
    project=Path(project).resolve();root=project.parent
    if output and Path(output).resolve().is_relative_to(root):raise ValueError('destination-inside-source')
    spec=importlib.util.spec_from_file_location('sc_lifecycle_old',HERE.parent/'resolve.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    config=c.load(project);old.validate(config,'project')
    plan_file=Path(plan_file).resolve();catalog_file=Path(catalog_file).resolve()
    plan=validate(c.load(plan_file),'plan');catalog=validate(c.load(catalog_file),'catalog')
    snapshots={p:c.raw_read(p) for p in (project,plan_file,catalog_file)}
    if plan['sourceProjectSha256']!=digest(snapshots[project]):raise ValueError('source-project-mismatch')
    changes={}
    for row in plan['changes']:
        p=c.confined(root,root,row['source']['path'])
        if p in changes:raise ValueError('duplicate-update-entry')
        if 'replacement' in row:raise ValueError('migration-does-not-accept-content-replacement')
        changes[p]=row
    for b in config['bindings']:old.resolve(project,b['prefix'])
    done={};active=set();files={};reports=[];missing=[]
    def convert(ref):
        path=c.confined(root,root,ref['path']);doc,raw=standard(path);snapshots[path]=raw
        if release(doc,raw)!={k:ref[k] for k in ('id','version','sha256')}:raise ValueError('source-standard-mismatch')
        if path in active:raise ValueError('inheritance-cycle')
        if path in done:return dict(done[path])
        if path not in changes:raise ValueError('missing-target-version: '+doc['id'])
        row=changes[path]
        if {k:row['source'][k] for k in ('id','version','sha256')}!=release(doc,raw):raise ValueError('source-standard-mismatch')
        if version(row['targetVersion'])<=version(doc['version']):raise ValueError('target-version-must-increase')
        active.add(path);new=copy.deepcopy(doc);new.update(formatVersion='1.0',version=row['targetVersion'])
        for ref2 in new.get('extends',[]):
            parent=convert(ref2);parent['path']=Path(os.path.relpath(root/parent['path'],path.parent)).as_posix()
            ref2.clear();ref2.update(parent)
        for ref2 in new.get('uses',[]):missing.append({'standard':new['id'],'uses':ref2['id'],'missing':'location'})
        content=c.dump(new).encode();pin=dict(release(new,content),path=path.relative_to(root).as_posix())
        for known in catalog['releases']:
            if (known['id'],known['version'])==(pin['id'],pin['version']) and known['sha256']!=pin['sha256']:raise ValueError('target-version-collision')
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'old.json';b=Path(tmp)/'new.json';a.write_bytes(raw);b.write_bytes(content)
            report=comparison(a,b)
        if not report['categorySufficient']:raise ValueError('insufficient-target-version-category')
        reports.append(report);files[pin['path']]=content;done[path]=pin;active.remove(path)
        return dict(pin)
    updated=copy.deepcopy(config);updated['formatVersion']='1.0'
    for binding in updated['bindings']:binding['standards']=[convert(r) for r in binding['standards']]
    if set(changes)!=set(done):raise ValueError('update-entry-not-reachable')
    if project.name in files:raise ValueError('output-path-collision')
    files[project.name]=c.dump(updated).encode()
    report={'format':'standard-contract-migration','formatVersion':'1.0','status':'candidate-requires-review',
            'comparisons':sorted(reports,key=c.dump),'missingInformation':sorted(missing,key=c.dump),
            'objectsCopied':False,'sourceModified':False,'newAdoptionReady':False,'files':sorted(files)}
    if 'lifecycle-report.json' in files:raise ValueError('output-path-collision')
    files['lifecycle-report.json']=c.dump(report).encode()
    with tempfile.TemporaryDirectory() as temp:install_tree(files,Path(temp)/'trial',snapshots)
    install_tree(files,output,snapshots);return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('compare');p.add_argument('old');p.add_argument('new');p.add_argument('--transition')
    p=sub.add_parser('impact');p.add_argument('project');p.add_argument('standard_id')
    for cmd in ('prepare','migrate1'):
        p=sub.add_parser(cmd);p.add_argument('project');p.add_argument('plan');p.add_argument('catalog');p.add_argument('--output')
        if cmd=='prepare':p.add_argument('--journal')
    p=sub.add_parser('status');p.add_argument('standard');p.add_argument('--journal')
    for cmd in ('evidence-template','evidence-check'):
        p=sub.add_parser(cmd);p.add_argument('project');p.add_argument('target');p.add_argument('--checker-id',required=True);p.add_argument('--checker-version',required=True)
        if cmd=='evidence-check':p.add_argument('receipt');p.add_argument('--journal')
    args=parser.parse_args()
    try:
        if args.command=='compare':result=comparison(args.old,args.new,args.transition)
        elif args.command=='impact':result=impact(args.project,args.standard_id)
        elif args.command=='prepare':result=prepare(args.project,args.plan,args.catalog,args.journal,args.output)
        elif args.command=='migrate1':result=migrate1(args.project,args.plan,args.catalog,args.output)
        elif args.command=='status':result=journal_status(args.journal,[release(*standard(args.standard))])
        elif args.command=='evidence-template':result=evidence_snapshot(args.project,args.target,args.checker_id,args.checker_version)
        else:result=evidence_check(args.project,args.target,args.receipt,args.checker_id,args.checker_version,args.journal)
        print(c.dump(result),end='')
        return 0
    except (ValueError,OSError,ValidationError,RecursionError) as exc:
        print(c.dump({'status':'error','message':exc.message if isinstance(exc,ValidationError) else str(exc)}),end='')
        return 1


if __name__=='__main__':raise SystemExit(main())
