#!/usr/bin/env python3
"""Resolve local pinned standards; optionally inspect a JSON artifact. Never edit it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def validate(value, name):
    Draft202012Validator(load(HERE / (name + '.schema.json'))).validate(value)


def relative(value):
    p = PurePosixPath(value)
    if not value or value.startswith('/') or '\\' in value or any(x in ('', '.', '..') for x in value.split('/')):
        raise ValueError('Expected normalized relative POSIX path: ' + value)
    return p


def resolve(project, target):
    project = Path(project).resolve()
    root = project.parent
    relative(target)
    config = load(project)
    validate(config, 'project')
    for binding in config['bindings']:
        relative(binding['prefix'])
    selected = [b for b in config['bindings'] if target == b['prefix'] or target.startswith(b['prefix'] + '/')]
    if not selected:
        raise ValueError('No binding for target')
    kinds = {b['kind'] for b in selected}
    if len(kinds) != 1:
        raise ValueError('Conflicting target kinds')
    kind = kinds.pop()
    seen, visiting, sources, rules, values = {}, set(), {}, {}, {}

    def visit(ref, depth=0):
        if depth > 64:
            raise ValueError('Dependency budget exceeded')
        path = (root / relative(ref['path'])).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Reference leaves project root')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise ValueError('Digest mismatch: ' + ref['path'])
        standard = load(path)
        validate(standard, 'standard')
        if standard['id'] != ref['id'] or standard['version'] != ref['version']:
            raise ValueError('Identity or version mismatch')
        sid = standard['id']
        identity = (standard['version'], ref['sha256'])
        if sid in visiting:
            raise ValueError('Dependency cycle')
        if sid in seen:
            if seen[sid] != identity:
                raise ValueError('Conflicting versions or content: ' + sid)
            return
        if len(seen) >= 256:
            raise ValueError('Dependency budget exceeded')
        if kind not in standard['appliesTo']:
            raise ValueError('Standard does not apply to target kind: ' + sid)
        visiting.add(sid)
        seen[sid] = identity
        for parent in standard.get('extends', []):
            visit(parent, depth + 1)
        visiting.remove(sid)
        sources[sid] = {'id': sid, 'version': identity[0], 'sha256': identity[1]}
        local = set()
        for rule in standard['requirements']:
            if rule['id'] in local:
                raise ValueError('Duplicate requirement: ' + rule['id'])
            local.add(rule['id'])
            key = sid + '#' + rule['id']
            rules[key] = dict(rule, source=sid, key=key)
            if rule['verification'] == 'equals':
                prop = rule['property']
                encoded = json.dumps(rule['value'], sort_keys=True, ensure_ascii=True, separators=(',', ':'))
                if prop in values and values[prop] != encoded:
                    raise ValueError('Conflicting mandatory values: ' + prop)
                values[prop] = encoded

    for binding in selected:
        relative(binding['prefix'])
        for ref in binding['standards']:
            visit(ref)
    return {'format': 'standard-contract-resolution', 'formatVersion': 'draft-1',
            'target': target, 'kind': kind,
            'standards': [sources[k] for k in sorted(sources)],
            'requirements': [rules[k] for k in sorted(rules)]}


def check(resolved, artifact):
    rows = []
    for rule in resolved['requirements']:
        status = 'needs-review'
        if rule['verification'] == 'equals':
            expected = json.dumps(rule['value'], sort_keys=True)
            actual = json.dumps(artifact.get(rule['property']), sort_keys=True)
            status = 'pass' if rule['property'] in artifact and actual == expected else 'fail'
        rows.append({'requirement': rule['key'], 'level': rule['level'], 'status': status})
    mandatory = [r for r in rows if r['level'] == 'must']
    verdict = 'fail' if any(r['status'] == 'fail' for r in mandatory) else (
        'needs-review' if any(r['status'] == 'needs-review' for r in mandatory) else 'pass')
    return {'status': verdict, 'requirements': rows, 'artifactModified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project'); p.add_argument('target'); p.add_argument('--artifact')
    args = p.parse_args()
    try:
        result = resolve(args.project, args.target)
        if args.artifact:
            artifact = load(Path(args.artifact))
            if not isinstance(artifact, dict):
                raise ValueError('Artifact must be a JSON object')
            result = check(result, artifact)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        return {'fail': 1, 'needs-review': 2}.get(result.get('status'), 0)
    except (ValueError, OSError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)})); return 1
    except Exception as exc:
        from jsonschema.exceptions import ValidationError
        if not isinstance(exc, ValidationError):
            raise
        print(json.dumps({'status': 'error', 'message': exc.message})); return 1


if __name__ == '__main__':
    raise SystemExit(main())
