#!/usr/bin/env python3
"""Local Standard Contract draft-2 resolver, declarations and artifact checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator, ValidationError

HERE = Path(__file__).resolve().parent
MAX_BYTES = 4 * 1024 * 1024


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate-json-key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('invalid-json-number: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def raw_read(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('file-size-limit')
    return raw


def load(path):
    return decode(raw_read(path))


def dump(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + '\n'


def validate(value, name):
    Draft202012Validator(load(HERE / (name + '.schema.json'))).validate(value)


def target_path(value):
    if not value or '\\' in value or ':' in value or value.startswith('/') or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('invalid-target-path: ' + value)
    return value


def confined(root, base, value):
    # Relative .. is useful for portable documents; the resolved root is the fence.
    if not value or value.startswith('/') or '\\' in value or ':' in value or '' in value.split('/'):
        raise ValueError('invalid-reference-path: ' + value)
    path = (base / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError('path-outside-bundle: ' + value)
    return path


def identity(ref):
    return (ref['id'], ref['version'], ref.get('sha256'))


def verify_ref(root, base, ref):
    if 'url' in ref:
        url = urlsplit(ref['url'])
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
            raise ValueError('invalid-source-url')
    if 'path' not in ref:
        return None, None
    path = confined(root, base, ref['path'])
    raw = raw_read(path)
    if hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('digest-mismatch: ' + ref['id'])
    return path, raw


def project_selection(project, target):
    project = Path(project).resolve()
    root = project.parent
    data = load(project); validate(data, 'project')
    for binding in data['bindings']:
        target_path(binding['prefix'])
    rows = [b for b in data['bindings'] if target == b['prefix'] or target.startswith(b['prefix'] + '/')]
    if not rows:
        raise ValueError('no-project-binding')
    kinds = {r['kind'] for r in rows}
    if len(kinds) != 1:
        raise ValueError('conflicting-target-kinds')
    return root, kinds.pop(), [ref for r in rows for ref in r['standards']]


def read_declaration(path, root, target_file):
    path = Path(path)
    actual = path.resolve()
    if not actual.is_relative_to(root):
        raise ValueError('declaration-outside-bundle')
    data = load(actual); validate(data, 'declaration')
    if data['target'] != target_file.name or '/' in data['target'] or '\\' in data['target']:
        raise ValueError('declaration-target-mismatch')
    if path.name != target_file.name + '.standards.json':
        raise ValueError('declaration-filename-mismatch')
    # Use the declaration's lexical directory; symlinks do not change link semantics.
    return data


class Resolver:
    def __init__(self, root):
        self.root = root
        self.loaded = {}
        self.active = set()
        self.rules = {}
        self.constraints = {}
        self.edges = []
        self.context = True

    def address(self, base, ref):
        result = {k: v for k, v in ref.items() if k != 'path'}
        if 'path' in ref:
            result['path'] = confined(self.root, base, ref['path']).relative_to(self.root).as_posix()
        return result

    def relation(self, source, relation, base, ref):
        address = self.address(base, ref)
        state = 'missing-location'
        if 'url' in ref:
            verify_ref(self.root, base, {k: v for k, v in ref.items() if k not in ('path', 'sha256')})
            state = 'not-fetched'
        if 'path' in ref:
            try:
                verify_ref(self.root, base, ref)
                state = 'verified-bytes'
            except FileNotFoundError:
                if relation != 'references':
                    raise ValueError('missing-local-dependency: ' + ref['id'])
                state = 'missing'
            except OSError:
                if relation != 'references':
                    raise
                state = 'unreadable'
            except ValueError as exc:
                if relation != 'references' or not str(exc).startswith('digest-mismatch:'):
                    raise
                state = 'digest-mismatch'
        if relation in ('uses', 'specification') and state != 'verified-bytes':
            self.context = False
        self.edges.append({'from': source, 'relation': relation, 'to': address, 'availability': state})

    def visit(self, base, ref, source='object', relation='selected', depth=0):
        if depth > 64:
            raise ValueError('dependency-depth-limit')
        path, raw = verify_ref(self.root, base, ref)
        if path is None:
            raise ValueError('local-standard-required')
        standard = decode(raw); validate(standard, 'standard')
        if (standard['id'], standard['version']) != (ref['id'], ref['version']):
            raise ValueError('identity-version-mismatch')
        sid = standard['id']; key = identity(ref)
        if sid in self.active:
            raise ValueError('inheritance-cycle')
        self.edges.append({'from': source, 'relation': relation, 'to': self.address(base, ref), 'availability': 'verified-bytes'})
        if sid in self.loaded:
            previous = self.loaded[sid]
            if previous['identity'] != key:
                raise ValueError('conflicting-standard-identity')
            if previous['path'] != path:
                # Identical relative-link documents in different directories can
                # point to different dependencies. Do not silently deduplicate them.
                raise ValueError('ambiguous-standard-location')
            return
        if len(self.loaded) >= 256:
            raise ValueError('standard-count-limit')
        if self.kind not in standard['appliesTo']:
            raise ValueError('inapplicable-standard: ' + sid)
        self.loaded[sid] = {'identity': key, 'path': path}
        self.active.add(sid)
        for parent in standard.get('extends', []):
            self.visit(path.parent, parent, sid, 'extends', depth + 1)
        self.active.remove(sid)
        for relation in ('uses', 'references'):
            for link in standard.get(relation, []):
                self.relation(sid, relation, path.parent, link)
        if 'specification' in standard:
            self.relation(sid, 'specification', path.parent, standard['specification'])
        local_ids = set()
        for rule in standard['requirements']:
            if rule['id'] in local_ids:
                raise ValueError('duplicate-requirement')
            local_ids.add(rule['id'])
            rid = sid + '#' + rule['id']
            self.rules[rid] = dict(rule, key=rid, source=sid, sourceVersion=ref['version'], sourceSha256=ref['sha256'])
            if rule['verification'] == 'equals':
                prop = rule['property']; value = dump(rule['value'])
                if prop in self.constraints and self.constraints[prop] != value:
                    raise ValueError('conflicting-mandatory-values: ' + prop)
                self.constraints[prop] = value

    def result(self, kind, target, entries):
        self.kind = kind
        for base, ref in entries:
            self.visit(base, ref)
        edges = {dump(edge): edge for edge in self.edges}
        return {'format': 'standard-contract-resolution', 'formatVersion': 'draft-2',
                'target': target, 'kind': kind,
                'normativeContext': 'available' if self.context else 'incomplete',
                'contextScope': 'inherited-standards-and-direct-contract-bytes',
                'artifactConformance': 'not-assessed',
                'relations': [edges[k] for k in sorted(edges)],
                'requirements': [self.rules[k] for k in sorted(self.rules)]}


def resolve(project, target):
    target_path(target)
    root, kind, refs = project_selection(project, target)
    target_file = confined(root, root, target)
    sidecar = Path(str(target_file) + '.standards.json')
    entries = [(root, ref) for ref in refs]
    if sidecar.exists() or sidecar.is_symlink():
        declaration = read_declaration(sidecar, root, target_file)
        if declaration['kind'] != kind or {identity(r) for r in refs} != {identity(r) for r in declaration['standards']}:
            raise ValueError('declaration-project-conflict')
        # Resolve independently: every sidecar pin and its relative dependencies
        # must work, even when project metadata selects the same identities.
        declared = Resolver(root).result(kind, target, [(sidecar.parent, r) for r in declaration['standards']])
        selected = Resolver(root).result(kind, target, entries)
        if declared['requirements'] != selected['requirements']:
            raise ValueError('declaration-context-conflict')
        # Include both proven address routes without changing requirements.
        unique = {dump(e): e for e in selected['relations'] + declared['relations']}
        selected['relations'] = [unique[k] for k in sorted(unique)]
        if declared['normativeContext'] == 'incomplete':
            selected['normativeContext'] = 'incomplete'
        selected['declaration'] = 'consistent'
        return selected
    result = Resolver(root).result(kind, target, entries)
    result['declaration'] = 'absent'
    return result


def standalone(declaration):
    declaration = Path(declaration).absolute()
    if not declaration.name.endswith('.standards.json'):
        raise ValueError('declaration-filename-mismatch')
    root = declaration.parent.resolve()
    target_file = declaration.with_name(declaration.name[:-len('.standards.json')])
    data = read_declaration(declaration, root, target_file)
    result = Resolver(root).result(data['kind'], data['target'], [(root, r) for r in data['standards']])
    result['declaration'] = 'standalone'
    return result


def prepare(project, target, write=False):
    target_path(target)
    root, kind, refs = project_selection(project, target)
    target_file = confined(root, root, target)
    result = Resolver(root).result(kind, target, [(root, r) for r in refs])
    unique = {}
    for ref in sorted(refs, key=dump):
        link = dict(ref)
        source = confined(root, root, ref['path'])
        link['path'] = Path(os.path.relpath(source, target_file.parent)).as_posix()
        unique[identity(ref)] = link
    declaration = {'format': 'standard-contract-declaration', 'formatVersion': 'draft-2',
                   'target': target_file.name, 'kind': kind,
                   'standards': [unique[k] for k in sorted(unique)]}
    validate(declaration, 'declaration')
    path = Path(str(target_file) + '.standards.json')
    if write:
        # Parent must already exist; exclusive create also refuses symlinks.
        with path.open('x', encoding='utf-8') as stream:
            stream.write(dump(declaration))
    return {'operation': 'declaration-created' if write else 'declaration-preview',
            'path': path.relative_to(root).as_posix(), 'declaration': declaration,
            'normativeContext': result['normativeContext']}


def check(resolution, artifact):
    if not isinstance(artifact, dict):
        raise ValueError('artifact-must-be-json-object')
    rows = []
    for rule in resolution['requirements']:
        state = 'needs-review'
        if rule['verification'] == 'equals':
            prop = rule['property']
            state = 'pass' if prop in artifact and dump(artifact[prop]) == dump(rule['value']) else 'fail'
        rows.append({'requirement': rule['key'], 'level': rule['level'], 'status': state})
    mandatory = [r for r in rows if r['level'] == 'must']
    verdict = 'fail' if any(r['status'] == 'fail' for r in mandatory) else (
        'needs-review' if resolution['normativeContext'] != 'available' or any(r['status'] == 'needs-review' for r in mandatory) else 'pass')
    return {'format': 'standard-contract-check', 'formatVersion': 'draft-2', 'status': verdict,
            'normativeContext': resolution['normativeContext'], 'requirements': rows, 'artifactModified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('resolve'); p.add_argument('project'); p.add_argument('target'); p.add_argument('--artifact')
    p = subs.add_parser('standalone'); p.add_argument('declaration'); p.add_argument('--artifact')
    p = subs.add_parser('declare'); p.add_argument('project'); p.add_argument('target'); p.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'declare':
            result = prepare(args.project, args.target, args.write)
        else:
            result = resolve(args.project, args.target) if args.command == 'resolve' else standalone(args.declaration)
            if args.artifact:
                result = check(result, load(args.artifact))
        print(dump(result), end='')
        return {'fail': 1, 'needs-review': 2}.get(result.get('status'), 0)
    except (ValueError, OSError, ValidationError, RecursionError) as exc:
        print(dump({'status': 'error', 'message': exc.message if isinstance(exc, ValidationError) else str(exc)}), end='')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
