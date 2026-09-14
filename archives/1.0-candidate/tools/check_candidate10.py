#!/usr/bin/env python3
"""Verify the exact files pinned by the AI First 1.0 candidate lock."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(lock_path=None):
    lock_path = Path(lock_path) if lock_path else ROOT / 'conformance/1.0/candidate.json'
    raw = lock_path.read_bytes()
    lock = json.loads(raw)
    errors = []
    seen = set()
    for row in lock['files']:
        name = row['path']
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or name in seen:
            errors.append({'path': name, 'error': 'unsafe-or-duplicate-path'})
            continue
        seen.add(name)
        target = (ROOT / path).resolve()
        if not target.is_relative_to(ROOT):
            errors.append({'path': name, 'error': 'path-leaves-root'})
            continue
        if not target.is_file():
            errors.append({'path': name, 'error': 'missing'})
            continue
        data = target.read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            errors.append({'path': name, 'error': 'digest-mismatch'})
    return {'candidate': lock['candidate'],
            'lockSha256': hashlib.sha256(raw).hexdigest(),
            'status': 'fail' if errors else 'pass',
            'files': len(seen), 'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock')
    try:
        result = verify(parser.parse_args().lock)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['status'] == 'pass' else 1)
    except (OSError, ValueError, KeyError):
        print(json.dumps({'status': 'fail', 'error': 'Candidate lock is unreadable or malformed'}))
        raise SystemExit(1)
