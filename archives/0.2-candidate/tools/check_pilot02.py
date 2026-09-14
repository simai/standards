#!/usr/bin/env python3
"""Inspect a returned local pilot receipt and publication compatibility.

Command logs are evidence to review, never shell commands to execute. A successful
check is not automatic acceptance of all product scenario claims.
"""
import argparse
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from aifirst import Failure, fail, strict_json
from aifirst02 import Reader
from check_candidate02 import ROOT, verify

SCENARIOS = {
    'docara': {'opt-in', 'real-docs', 'multilingual', 'code-tables-components',
               'full-build', 'single-page-build', 'page-deletion', 'error-preserves-output', 'joint-export'},
    'larena': {'documentation', 'operation-binding', 'guest', 'allowed-user',
               'denied-user', 'other-organization', 'no-business-execution', 'access-isolation'}
}


def check(receipt_file, artifact_root):
    root = Path(artifact_root).resolve()
    receipt = strict_json(Path(receipt_file).read_bytes())
    schema = json.loads((ROOT/'schemas/0.2/pilot-result.schema.json').read_text())
    if list(Draft202012Validator(schema).iter_errors(receipt)):
        fail('invalid-receipt', 'Receipt does not match the pilot result schema')
    candidate = verify()
    if candidate['status'] != 'pass' or receipt['candidate'] != candidate['candidate'] or receipt['candidateLockSha256'] != candidate['lockSha256']:
        fail('candidate-mismatch', 'Pilot does not bind to the current frozen candidate')
    def artifact(name):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            fail('invalid-receipt', 'Artifact path must be relative and confined')
        result = (root/relative).resolve()
        if not result.is_relative_to(root):
            fail('access-blocked', 'Artifact path leaves the returned bundle')
        return result
    names = set()
    for row in receipt['artifacts']:
        if row['path'] in names: fail('invalid-receipt', 'Duplicate artifact path')
        names.add(row['path'])
        if hashlib.sha256(artifact(row['path']).read_bytes()).hexdigest() != row['sha256']:
            fail('digest-mismatch', 'Returned artifact digest differs')
    scenarios = {s['id']: s for s in receipt['scenarios']}
    if len(scenarios) != len(receipt['scenarios']) or not SCENARIOS[receipt['product']].issubset(scenarios):
        fail('invalid-receipt', 'Missing or duplicate required scenarios')
    for scenario in scenarios.values():
        if not set(scenario['evidence']).issubset(names):
            fail('invalid-receipt', 'Scenario evidence is not in the hashed inventory')
    for command in receipt['commands']:
        if command['evidence'] not in names:
            fail('invalid-receipt', 'Command evidence is not in the hashed inventory')
    reports = []
    for entry in receipt['publications']:
        target = artifact(entry)
        manifest = target/'ai.json' if target.is_dir() else target
        manifest_name = manifest.relative_to(root).as_posix()
        if manifest_name not in names:
            fail('invalid-receipt', 'Publication manifest must be hashed')
        reader = Reader(manifest)
        reader.discover('manifest'); reader.inventory(); report = reader.publication()
        # Every byte used for compatibility must belong to the returned inventory.
        from urllib.parse import unquote, urlsplit
        for retrieved in reader.transport.records:
            p = Path(unquote(urlsplit(retrieved['finalUrl']).path)).resolve()
            if not p.is_relative_to(root) or p.relative_to(root).as_posix() not in names:
                fail('invalid-receipt', 'Read publication file is not in the hashed inventory')
        reports.append({'entry': entry, 'publication': report['publication'], 'errors': report['errors']})
    problems = [s['id'] for s in scenarios.values() if s['status'] != 'pass']
    return {'product': receipt['product'], 'candidate': receipt['candidate'],
            'receiptIntegrity': 'pass', 'publications': reports,
            'publicationCompatibility': 'pass' if all(r['publication'] == 'pass' for r in reports) else 'fail',
            'scenarioClaimsRequiringReview': problems,
            'scenarioEvidenceReview': 'pending-human-or-owner-review',
            'pilotAcceptance': 'pending', 'commandsExecuted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('receipt'); p.add_argument('artifacts')
    args = p.parse_args()
    try:
        result = check(args.receipt, args.artifacts); print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['publicationCompatibility'] == 'pass' else 1)
    except (Failure, OSError, ValueError) as exc:
        print(json.dumps({'status': 'fail', 'error': exc.record() if isinstance(exc, Failure) else {'code': 'unreadable-receipt'}, 'pilotAcceptance': 'pending'}))
        raise SystemExit(1)
