#!/usr/bin/env python3
"""Convert a draft-1 project and reachable standards to a new 1.0 directory."""
import argparse
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import shutil
from contract import load, dump, validate, confined, raw_read

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('standard_contract_v1', HERE.parent / 'resolve.py')
v1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)


def migrate(project, destination=None):
    project = Path(project).resolve(); root = project.parent
    config = load(project); v1.validate(config, 'project')
    # Validate each binding independently of overlap selection before conversion.
    for binding in config['bindings']:
        v1.resolve(project, binding['prefix'])
    files, converted, active, missing, versions = {}, {}, set(), [], []

    def convert(ref):
        path = confined(root, root, ref['path'])
        if path in active:
            raise ValueError('inheritance-cycle')
        original = raw_read(path)
        if hashlib.sha256(original).hexdigest() != ref['sha256']:
            raise ValueError('draft-1-digest-mismatch')
        doc = load(path); v1.validate(doc, 'standard')
        if (doc['id'], doc['version']) != (ref['id'], ref['version']):
            raise ValueError('draft-1-identity-mismatch')
        name = path.relative_to(root).as_posix()
        if path not in converted:
            active.add(path)
            updated = copy.deepcopy(doc); updated['formatVersion'] = '1.0'
            parts = [int(x) for x in doc['version'].split('.')]
            parts[2] += 1
            updated['version'] = '.'.join(map(str, parts))
            versions.append({'id': doc['id'], 'from': doc['version'], 'to': updated['version']})
            for parent in updated.get('extends', []):
                new = convert(parent)
                new['path'] = Path(os.path.relpath(root / new['path'], path.parent)).as_posix()
                parent.clear(); parent.update(new)
            for link in updated.get('uses', []):
                missing.append({'standard': doc['id'], 'relation': 'uses', 'id': link['id'],
                                'version': link['version'], 'missing': ['path-or-url']})
            validate(updated, 'standard')
            content = dump(updated)
            files[name] = content
            converted[path] = {'id': doc['id'], 'version': updated['version'], 'path': name,
                               'sha256': hashlib.sha256(content.encode()).hexdigest()}
            active.remove(path)
        return dict(converted[path])

    new_config = copy.deepcopy(config); new_config['formatVersion'] = '1.0'
    for binding in new_config['bindings']:
        binding['standards'] = [convert(r) for r in binding['standards']]
    validate(new_config, 'project')
    if project.name in files or 'migration-report.json' in files or project.name == 'migration-report.json':
        raise ValueError('migration-output-collision')
    files[project.name] = dump(new_config)
    report = {'format': 'standard-contract-migration', 'formatVersion': '1.0',
              'sourceProjectSha256': hashlib.sha256(raw_read(project)).hexdigest(),
              'versionChanges': sorted(versions, key=dump), 'files': sorted(files), 'missingInformation': sorted(missing, key=dump),
              'artifactsCopied': False, 'sourceModified': False,
              'publicationStatus': 'unpublished-patch-versions-reserve-before-publication'}
    if destination is not None:
        dest = Path(destination).absolute()
        if dest.exists() or dest.is_symlink():
            raise ValueError('destination-already-exists')
        if dest.resolve().is_relative_to(root):
            raise ValueError('destination-inside-source')
        if not dest.parent.is_dir():
            raise ValueError('destination-parent-missing')
        staging = Path(tempfile.mkdtemp(prefix='.standard-contract-', dir=dest.parent))
        try:
            for name, content in files.items():
                out = staging / name; out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(content)
            (staging / 'migration-report.json').write_text(dump(report))
            from contract import resolve
            for binding in new_config['bindings']:
                resolve(staging / project.name, binding['prefix'])
            # Exclusive destination reservation; never overwrite an existing tree.
            dest.mkdir()
            try:
                for child in staging.iterdir():
                    shutil.move(str(child), str(dest / child.name))
            except Exception:
                shutil.rmtree(dest)
                raise
        finally:
            shutil.rmtree(staging)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project'); p.add_argument('--output', help='Create a new directory; omit for preview')
    a = p.parse_args()
    try:
        print(dump(migrate(a.project, a.output)), end='')
    except Exception as exc:
        from jsonschema import ValidationError
        if not isinstance(exc, (ValueError, OSError, ValidationError, RecursionError)):
            raise
        print(dump({'status': 'error', 'message': str(exc)}), end='')
        raise SystemExit(1)
