#!/usr/bin/env python3
"""Verify the combined release inventory; does not claim object conformance."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RELEASE = '1.1.0'
STANDARDS = {'ai-first': '1.0.0', 'standard-contract': '1.0.0', 'standard-contract-lifecycle': '1.0.0', 'simai.linkage': '1.1.0', 'simai.change-lifecycle': '1.1.0'}

def verify(root=ROOT):
    root = Path(root).resolve()
    lock = json.loads((root / 'release-manifest.json').read_text())
    errors = []
    seen = set()
    if lock.get('release') != RELEASE or lock.get('standards') != STANDARDS:
        errors.append('invalid-release-identity')
    for row in lock['files']:
        p = Path(row['path'])
        if p.is_absolute() or '..' in p.parts or str(p) in seen:
            errors.append('unsafe-or-duplicate-path'); continue
        seen.add(str(p))
        target = (root / p).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(str(p) + ': missing-or-unsafe'); continue
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256'] or len(data) != row['bytes']:
            errors.append(str(p) + ': digest-mismatch')
    if not seen: errors.append('empty-release')
    return {'release': lock.get('release'), 'status': 'fail' if errors else 'pass',
            'files': len(seen), 'errors': errors, 'authenticity': 'not-assessed'}

if __name__ == '__main__':
    try:
        result = verify(); print(json.dumps(result, indent=2))
        sys.exit(0 if result['status'] == 'pass' else 1)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'fail', 'error': str(exc)})); sys.exit(1)
