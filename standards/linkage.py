#!/usr/bin/env python3
"""Reference implementation of simai.linkage 1.1.0 and simai.change-lifecycle 1.1.0.

Validates the core formats (Framework 1.0.0 formats are read as profile
framework), takes a content hash, compares two inventories and reconciles a
usage record against inventories as of a date, following chains across sources.
It never changes the consumer; every result is data.
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
FORMATS = {
    'simai.unit-passport': 'unit-passport', 'simai.framework.unit-passport': 'unit-passport',
    'simai.unit-inventory': 'unit-inventory', 'simai.framework.unit-inventory': 'unit-inventory',
    'simai.unit-change-report': 'unit-change-report', 'simai.framework.unit-change-report': 'unit-change-report',
    'simai.usage-record': 'usage-record', 'simai.reconcile-report': 'reconcile-report',
    'simai.change-journal': 'change-journal', 'simai.change-journal.v1': 'change-journal',
}
FRAMEWORK = {'id': 'framework', 'version': '1.0.0'}
# Worst first: a place gets the first status any of its paths reaches.
ORDER = ['missing', 'action-needed', 'former-name', 'unverified', 'update-available', 'upcoming', 'kept', 'current']
NORMALIZATION = 'simai.text/1: Unicode NFC, every run of white space one space, trimmed'


def _registry():
    resources = []
    for path in sorted((HERE / 'schemas').glob('*.json')) + sorted((HERE / 'pinned').glob('*.json')):
        schema = json.loads(path.read_text())
        resources.append((schema['$id'], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


REGISTRY = _registry()


def schema_for(name):
    return json.loads((HERE / 'schemas' / f'{name}-1.0.0.schema.json').read_text())


def validate(doc):
    """Errors of a document against its core format; [] when valid."""
    name = FORMATS.get(doc.get('schema')) if isinstance(doc, dict) else None
    if not name:
        return [f"unknown format {doc.get('schema') if isinstance(doc, dict) else type(doc).__name__}"]
    validator = Draft202012Validator(schema_for(name), registry=REGISTRY)
    return [f"{'/'.join(map(str, e.absolute_path)) or '.'}: {e.message}" for e in validator.iter_errors(doc)]


def profile_of(doc):
    """simai.linkage profile-declared: explicit, or implied by a Framework schema id."""
    if doc.get('profile'):
        return doc['profile']
    if doc.get('schema', '').startswith('simai.framework.') or doc.get('schema') in ('simai.change-journal', 'simai.change-journal.v1'):
        return FRAMEWORK
    return None


# Content hash -----------------------------------------------------------------

def hash_git_files(paths, repo, rev='HEAD'):
    """1.0.0 content-hash: for each file in ascending path order its path, a zero
    byte, its length in decimal, a zero byte, then its bytes, read from git."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.encode()):
        data = subprocess.run(['git', '-C', str(repo), 'show', f'{rev}:{path}'], check=True, capture_output=True).stdout
        digest.update(path.encode() + b'\0' + str(len(data)).encode() + b'\0' + data)
    return digest.hexdigest()


def normalize_text(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def hash_normalized_text(text):
    return hashlib.sha256(normalize_text(text).encode()).hexdigest()


# Versions ------------------------------------------------------------------

def _semver(v):
    return tuple(int(x) for x in v.split('.'))


def step(old, new):
    """major, minor or patch for semver; edition for dates; sequence for integers."""
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', old) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', new):
        return 'edition'
    if old.isdigit() and new.isdigit():
        return 'sequence'
    a, b = _semver(old), _semver(new)
    return 'major' if b[0] != a[0] else 'minor' if b[1] != a[1] else 'patch'


def newer(old, new):
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', old) or old.isdigit():
        return (int(new) > int(old)) if old.isdigit() else new > old
    return _semver(new) > _semver(old)


# Inventories ---------------------------------------------------------------

def compare(a, b, journal=None):
    """simai.linkage inventories-compare: two inventories of one source → change report."""
    units_a = {u['id']: u for u in a['units']}
    units_b = {u['id']: u for u in b['units']}
    changed, violations = [], []
    if a['source'] != b['source']:
        violations.append({'id': b['source'], 'code': 'source-differs'})
    records = (journal or {}).get('records', [])
    for uid in sorted(set(units_a) & set(units_b)):
        ua, ub = units_a[uid], units_b[uid]
        if ua['content_sha256'] == ub['content_sha256'] and ua['version'] == ub['version']:
            continue
        if ua['version'] == ub['version']:
            violations.append({'id': uid, 'code': 'hash-moved-without-version'})
            continue
        if not newer(ua['version'], ub['version']):
            violations.append({'id': uid, 'code': 'version-went-back'})
            continue
        entry = {'id': uid, 'from_version': ua['version'], 'to_version': ub['version'], 'step': step(ua['version'], ub['version'])}
        anchors_a = {x['id']: x.get('content_sha256') for x in ua.get('anchors', [])}
        moved = [x['id'] for x in ub.get('anchors', []) if anchors_a.get(x['id'], '') != x.get('content_sha256')]
        if moved:
            entry['anchors'] = moved
        hits = [r['id'] for r in records if any(i.get('unit') == uid or i.get('component') == uid for i in r['items'])]
        if hits:
            entry['journal'] = hits
        changed.append(entry)
    moved_ids = {c['id'] for c in changed}
    deps_changed = []
    for uid, ub in sorted(units_b.items()):
        moved = sorted(d['id'] for d in ub.get('dependencies', []) if d['id'] in moved_ids)
        if moved and uid not in moved_ids:
            deps_changed.append({'id': uid, 'moved': moved})
    return {'schema': 'simai.unit-change-report', 'schema_version': 1, 'profile': profile_of(b) or FRAMEWORK,
            'source': b['source'], 'from': a.get('release') or a.get('revision', ''), 'to': b.get('release') or b.get('revision', ''),
            'added': sorted(set(units_b) - set(units_a)), 'removed': sorted(set(units_a) - set(units_b)),
            'changed': changed, 'dependencies_changed': deps_changed, 'violations': violations}


# Reconcile -----------------------------------------------------------------

def _edition_on(unit, date):
    """The edition of a dated unit in force on a date: (version, edition)."""
    editions = [*unit.get('history', []), unit['edition']] if unit.get('edition') else unit.get('history', [])
    found = None
    for e in sorted(editions, key=lambda e: e['since']):
        if e['since'] <= date and (not e.get('effective_to') or e['effective_to'] > date):
            found = e
    return found


def _impact(profile, dep, unit, current_step, journal_hits):
    """Profile impact rule: update-available or action-needed."""
    pid = (profile or FRAMEWORK)['id']
    if pid == 'norms' or unit.get('force'):
        if unit.get('force') == 'mandatory' and dep.get('relation') in ('deviates', 'restates'):
            return 'action-needed'
        return 'update-available'
    if current_step == 'major' or journal_hits:
        return 'action-needed'
    return 'update-available'


class Reconciler:
    """Reconcile a usage record against inventories of one or more sources."""

    def __init__(self, inventories, journals=(), as_of=None, baselines=()):
        # Baselines: inventories of the releases the record was last brought up to,
        # so a changed foundation is found even when the used unit did not move.
        self.before = {}
        for inv in baselines:
            for u in inv['units']:
                self.before[f"{inv['source']}:{u['id']}"] = u
                self.before.setdefault(u['id'], u)
        self.units = {}
        self.profiles = {}
        for inv in inventories:
            for u in inv['units']:
                self.units[f"{inv['source']}:{u['id']}"] = u
                self.units.setdefault(u['id'], u)
                self.profiles[u['id']] = self.profiles[f"{inv['source']}:{u['id']}"] = profile_of(inv)
        self.former = {}
        for unit_id, u in list(self.units.items()):
            for f in u.get('former_ids', []):
                self.former[f['id']] = (unit_id, f['journal'])
        self.journal = [r for j in journals for r in j.get('records', [])]
        self.as_of = as_of or datetime.date.today().isoformat()

    def _journal_for(self, uid, from_version):
        return [r for r in self.journal if r['stage'] == 'compat' and any(i.get('unit') == uid or i.get('component') == uid for i in r['items'])]

    def _deps(self, uid, made_on, path, seen, out):
        """Follow declared dependencies (foundations within a source, chains across sources)."""
        unit = self.units.get(uid)
        if not unit or uid in seen:
            return
        seen = seen | {uid}
        for dep in unit.get('dependencies', []) + [d for a in unit.get('anchors', []) for d in a.get('dependencies', [])]:
            target = self.units.get(dep['id'])
            hop = [dep['id'] + (f"#{dep['from']}" if dep.get('from') else '')] + path
            if target is None:
                out.append({'status': 'missing', 'path': hop})
                continue
            if dep.get('constraint') == 'in-force':
                out.extend(self._dated(dep, target, made_on, hop))
            elif dep.get('range') and not _semver(target['version'])[0] == _semver(dep['range'][1:])[0]:
                out.append({'status': 'action-needed', 'path': hop, 'to_version': target['version']})
            elif dep['id'] in self.before and self.before[dep['id']]['content_sha256'] != target['content_sha256']:
                old = self.before[dep['id']]['version']
                hits = self._journal_for(dep['id'], old)
                st = step(old, target['version']) if old != target['version'] else 'patch'
                out.append({'status': _impact(self.profiles.get(dep['id']), dep, target, st, hits), 'path': hop,
                            'from_version': old, 'to_version': target['version']})
            self._deps(dep['id'], made_on, hop, seen, out)

    def _dated(self, dep, unit, made_on, path):
        then = _edition_on(unit, made_on) if made_on else None
        now = _edition_on(unit, self.as_of)
        found = []
        if then and now and then['since'] != now['since']:
            status = 'unverified' if now.get('status') == 'candidate' else _impact(self.profiles.get(dep['id']), dep, unit, 'edition', [])
            found.append({'status': status, 'path': path, 'from_version': then['since'], 'to_version': now['since'], 'effective_from': now['since'],
                          'instruction': f"{now['by']}"})
        later = [e for e in [*unit.get('history', []), unit.get('edition') or {}] if e and e['since'] > self.as_of]
        for e in later:
            found.append({'status': 'unverified' if e.get('status') == 'candidate' else 'upcoming', 'path': path,
                          'to_version': e['since'], 'effective_from': e['since'], 'instruction': e['by']})
        # simai.linkage 15: a mirrored unit never compared with its source is shown.
        if not unit.get('checked') and (self.profiles.get(dep['id']) or {}).get('id') == 'norms':
            found.append({'status': 'unverified', 'path': path})
        return found

    def place(self, p):
        uid = p['unit']
        base = {'place': p['place'], 'unit': uid}
        if uid not in self.units:
            if uid in self.former:
                new_id, journal = self.former[uid]
                rec = next((r for r in self.journal if r['id'] == journal), {})
                return {**base, 'status': 'former-name', 'path': [uid, p['place']], 'replaced_by': new_id,
                        **({'stops_on': rec.get('extended_to') or rec['remove_after']} if rec else {})}
            return {**base, 'status': 'missing', 'path': [uid, p['place']]}
        unit = self.units[uid]
        results = []
        if unit['content_sha256'] != p['content_sha256'] and unit['version'] != p['version']:
            hits = self._journal_for(uid, p['version'])
            st = step(p['version'], unit['version'])
            status = _impact(self.profiles.get(uid), {}, unit, st, hits)
            entry = {'status': status, 'path': [uid, p['place']], 'from_version': p['version'], 'to_version': unit['version']}
            if hits and hits[0].get('manual'):
                entry['instruction'] = hits[0]['manual']
            results.append(entry)
        self._deps(uid, p.get('made_on'), [uid, p['place']], set(), results)
        if p.get('kept'):
            for r in results:
                if r['status'] in ('update-available', 'action-needed'):
                    r['status'] = 'kept'
        if not results:
            return {**base, 'status': 'current', 'path': [uid, p['place']]}
        worst = min(results, key=lambda r: ORDER.index(r['status']))
        return {**base, **worst}

    def report(self, record):
        return {'schema': 'simai.reconcile-report', 'schema_version': 1, 'consumer': record['consumer'], 'as_of': self.as_of,
                'places': [self.place(p) for p in record['places']]}


def reconcile(record, inventories, journals=(), as_of=None, baselines=()):
    return Reconciler(inventories, journals, as_of, baselines).report(record)


# Command line --------------------------------------------------------------

def _load(path):
    return json.loads(Path(path).read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    v = sub.add_parser('validate', help='validate documents against the core formats')
    v.add_argument('files', nargs='+')
    c = sub.add_parser('compare', help='two inventories of one source → change report')
    c.add_argument('from_inventory')
    c.add_argument('to_inventory')
    c.add_argument('--journal')
    r = sub.add_parser('reconcile', help='usage record + inventories → reconcile report')
    r.add_argument('record')
    r.add_argument('inventories', nargs='+')
    r.add_argument('--journal', action='append', default=[])
    r.add_argument('--as-of')
    r.add_argument('--baseline', action='append', default=[], help='inventory of the release the record was brought up to')
    h = sub.add_parser('hash-text', help='normalized-text content hash of a file')
    h.add_argument('file')
    args = parser.parse_args(argv)
    if args.command == 'validate':
        bad = 0
        for f in args.files:
            errors = validate(_load(f))
            bad += bool(errors)
            print(('ok   ' if not errors else 'FAIL ') + f + ''.join('\n  ' + e for e in errors[:5]))
        return 1 if bad else 0
    if args.command == 'compare':
        report = compare(_load(args.from_inventory), _load(args.to_inventory), _load(args.journal) if args.journal else None)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if report['violations'] else 0
    if args.command == 'reconcile':
        report = reconcile(_load(args.record), [_load(i) for i in args.inventories], [_load(j) for j in args.journal], args.as_of,
                           [_load(b) for b in args.baseline])
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(hash_normalized_text(Path(args.file).read_text(encoding='utf-8')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
