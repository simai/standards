#!/usr/bin/env python3
"""Preflight-first local migration and joint AI First/llms.txt export.

A new output directory is mandatory. Only explicitly referenced local files
are copied, and all relative paths are preserved. No source changes or network
retrieval are performed. Dry-run is the default.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
from aifirst import Reader as Reader01, Failure, fail, resolve, strict_json
from aifirst02 import Reader as Reader02
from aifirst02_core import structure


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


class Capture01(Reader01):
    def __init__(self, entry):
        super().__init__(entry)
        self.payloads = {}; self.descriptors = {}

    def fetch(self, url, media=None, descriptor=False):
        if urlsplit(url).scheme != 'file':
            fail('migration-input', 'Offline migration cannot retrieve external content')
        data = super().fetch(url, media, descriptor)
        if url in self.payloads and self.payloads[url] != data:
            fail('revision-mismatch', 'Source changed during preflight')
        self.payloads[url] = data
        return data

    def document(self, url, expected):
        doc = super().document(url, expected)
        self.descriptors[url] = doc
        return doc


def local_name(root, url):
    p = urlsplit(url)
    if p.scheme != 'file' or p.netloc or p.query:
        fail('migration-input', 'Expected a local portable reference')
    path = Path(unquote(p.path)).resolve()
    if not path.is_relative_to(root):
        fail('access-blocked', 'Reference leaves the source root')
    return path.relative_to(root).as_posix()


def build_migration(source):
    source = Path(source).resolve()
    entry = source/'ai.json' if source.is_dir() else source
    root = entry.parent
    reader = Capture01(root)
    queue = [entry.as_uri()]; seen = set()
    while queue:
        url = queue.pop(0)
        if url in seen: continue
        seen.add(url); reader.entry = url
        reader.discover('manifest'); reader.inventory()
        result = reader.publication()
        if result['errors']:
            fail('migration-preflight', '0.1 publication validation failed: ' + result['errors'][0]['code'])
        queue.extend(resolve(reader.base, route['href']) for route in reader.manifest.get('routes', []))
    documents = copy.deepcopy(reader.descriptors)
    manual = []
    for url, doc in documents.items():
        # Optional 0.1 data may use names which acquire meaning in 0.2.
        if any(k in doc for k in ('access', 'related')) or any(
                'translationOf' in i for i in doc.get('items', [])) or any(
                'select' in link for link in doc.get('catalogs', [])):
            fail('migration-collision', 'A formerly optional field needs explicit 0.2 review')
        doc['formatVersion'] = '0.2'
        if doc.get('catalogs'):
            manual.append({'document': local_name(root, url), 'topic': 'catalog-selectors',
                           'action': 'Optional: add verified exhaustive bounds to enable selective reading.'})
        if any(i['language'].lower() != doc.get('resource', {}).get('language', '').lower()
               for i in doc.get('items', [])):
            manual.append({'document': local_name(root, url), 'topic': 'translations',
                           'action': 'Optional: assign reviewed language-neutral identities; never infer equivalence.'})
    completed = {}; active = set()
    def convert(url):
        if url in active: fail('cycle', 'Descriptor cycle during migration')
        if url in completed: return completed[url]
        active.add(url); doc = documents[url]
        for link in doc.get('catalogs', []):
            child_url = resolve(url, link['href'])
            child_data = convert(child_url)
            link['revision'] = documents[child_url]['revision']
            link['sha256'] = hashlib.sha256(child_data).hexdigest()
        structure(doc)
        data = encoded(doc); completed[url] = data; active.remove(url)
        return data
    for url in documents: convert(url)
    files = {local_name(root, url): data for url, data in reader.payloads.items()}
    files.update({local_name(root, url): data for url, data in completed.items()})
    manual.extend([{'topic': 'access-and-related-resources',
                    'action': 'Optional: publisher reviews access hints and related-resource links; none inferred.'},
                   {'topic': 'transport-discovery',
                    'action': 'Configure headers, CORS and caching on the actual server; not inferred from files.'}])
    return files, entry.name, manual


def build_export(source):
    """Export an existing local 0.2 inventory and exact representations together.

    The input manifest is the one source for AI First and llms.txt metadata.
    It can be produced by a site's existing Document IR or operation registry.
    """
    source = Path(source).resolve()
    entry = source/'ai.json' if source.is_dir() else source
    root = entry.parent
    reader = Reader02(root)
    payloads = {}; documents = {}; catalogs = {}; manifest_items = {}
    original_fetch = reader.transport.fetch
    def capture(url, media=None, descriptor=False):
        if urlsplit(url).scheme != 'file':
            fail('export-input', 'Portable export requires local referenced content')
        response = original_fetch(url, media, descriptor)
        name = local_name(root, response.url)
        if name in payloads and payloads[name] != response.data:
            fail('revision-mismatch', 'Source changed during preflight')
        payloads[name] = response.data
        if descriptor and media == 'application/json':
            doc = strict_json(response.data)
            if doc.get('document') == 'manifest': documents[response.url] = doc
        return response
    reader.transport.fetch = capture
    queue = [entry.as_uri()]; seen = set()
    while queue:
        url = queue.pop(0)
        if url in seen: continue
        seen.add(url); reader.entry = url; reader.discover('manifest'); reader.inventory()
        result = reader.publication()
        if result['errors']:
            fail('export-preflight', 'Publication validation failed: ' + result['errors'][0]['code'])
        manifest_items[url] = list(reader.report['items'])
        queue.extend(resolve(reader.base, r['href']) for r in reader.manifest.get('routes', []))
    for url, items in manifest_items.items():
        doc = documents[url]
        folder = Path(local_name(root, url)).parent
        name = (folder/'llms.txt').as_posix()
        if name in payloads or (root/name).exists():
            fail('export-collision', 'An existing llms.txt requires explicit reconciliation')
        lines = ['# ' + one_line(doc['resource']['name']), '',
                 '> ' + one_line(doc['resource']['description']), '', '## Documentation', '']
        for i, base in items:
            if i['status'] != 'published': continue
            reps = [r for r in i['representations'] if r.get('role', 'full') == 'full'
                    and r['mediaType'] in ('text/markdown', 'text/plain')]
            if not reps:
                fail('export-input', 'Joint text export needs a full Markdown/plain representation for each published item')
            target = resolve(base, reps[0]['href'])
            path = local_name(root, target)
            # The target is inside root. relpath only creates portable navigation
            # inside the exported tree, never an additional source read.
            href = Path(os.path.relpath(path, str(folder))).as_posix()
            label = one_line(i['title']).replace('[', '\\[').replace(']', '\\]')
            lines.append(f'- [{label}](<{href}>): ' + one_line(i['description']))
        payloads[name] = ('\n'.join(lines) + '\n').encode()
    return payloads, entry.name, []


def one_line(value):
    return ' '.join(value.split())


def prepare(source, output, mode):
    source = Path(source).resolve()
    root = source if source.is_dir() else source.parent
    output = Path(output).absolute()
    # Do not accept a symlink destination or source-overlapping output.
    if output.exists() or output.is_symlink():
        fail('output-exists', 'Output must be a new directory')
    if output.resolve().is_relative_to(root) or root.is_relative_to(output.resolve()):
        fail('invalid-output', 'Source and output trees must not overlap')
    if not output.parent.is_dir():
        fail('invalid-output', 'Output parent must already exist')
    files, entry, manual = build_migration(source) if mode == 'migrate' else build_export(source)
    for name in files:
        p = Path(name)
        if p.is_absolute() or '..' in p.parts:
            fail('invalid-output', 'Unsafe generated path')
    report = {'operation': mode, 'status': 'preflight-pass', 'written': False,
              'entry': entry, 'wireVersion': '0.2', 'manualReview': manual,
              'files': [{'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                        for name, data in sorted(files.items())]}
    return files, report


def publish(source, output, mode, apply=False):
    files, report = prepare(source, output, mode)
    if not apply: return report
    output = Path(output).absolute()
    staging = Path(tempfile.mkdtemp(prefix='.ai-first-stage-', dir=output.parent))
    try:
        for name, data in files.items():
            dest = staging/name; dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        candidate = Reader02(staging/report['entry'])
        candidate.discover('manifest'); candidate.inventory()
        validation = candidate.publication()
        if validation['errors']:
            fail('output-validation', 'Staged publication did not validate')
        # mkdir is the exclusive claim; never replace a concurrent output.
        output.mkdir()
        try:
            for child in staging.iterdir(): shutil.move(str(child), str(output/child.name))
        except Exception:
            # Only the output this call exclusively created can be removed.
            shutil.rmtree(output)
            raise
        report.update(status='written', written=True)
        return report
    finally:
        shutil.rmtree(staging)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['migrate', 'export'])
    p.add_argument('source'); p.add_argument('output')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    try:
        print(json.dumps(publish(args.source, args.output, args.mode, args.apply), indent=2))
        return 0
    except Failure as exc:
        print(json.dumps({'status': 'failed', 'error': exc.record(), 'written': False}))
        return 1


if __name__ == '__main__': raise SystemExit(main())
