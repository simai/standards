#!/usr/bin/env python3
"""Migrate a local AI First 0.2 publication to wire 1.0.

The operation is dry-run by default and writes only to a new output directory.
The 1.0 wire contract preserves 0.2 meaning, so migration changes descriptor
versions and recalculates catalog pins without inventing publication facts.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urlsplit

from aifirst import Failure, fail, resolve, strict_json
from aifirst02 import Reader as Reader02
from aifirst10 import Reader as Reader10
from aifirst10_core import structure


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def local_name(root, url):
    parsed = urlsplit(url)
    if parsed.scheme != 'file' or parsed.netloc or parsed.query:
        fail('migration-input', 'Migration accepts local portable references only')
    path = Path(unquote(parsed.path)).resolve()
    if not path.is_relative_to(root):
        fail('access-blocked', 'Reference leaves the source root')
    return path.relative_to(root).as_posix()


def build(source):
    source = Path(source).resolve()
    entry = source / 'ai.json' if source.is_dir() else source
    root = entry.parent
    reader = Reader02(root)
    payloads = {}
    documents = {}
    original_fetch = reader.transport.fetch

    def capture(url, media=None, descriptor=False):
        if urlsplit(url).scheme != 'file':
            fail('migration-input', 'Migration cannot retrieve network content')
        response = original_fetch(url, media, descriptor)
        name = local_name(root, response.url)
        if name in payloads and payloads[name] != response.data:
            fail('revision-mismatch', 'Source changed during preflight')
        payloads[name] = response.data
        if descriptor:
            document = strict_json(response.data)
            if document.get('document') in ('manifest', 'catalog'):
                documents[response.url] = document
        return response

    reader.transport.fetch = capture
    queue = [entry.as_uri()]
    seen = set()
    while queue:
        requested = queue.pop(0)
        if requested in seen:
            continue
        seen.add(requested)
        reader.entry = requested
        reader.discover('manifest')
        reader.inventory()
        validation = reader.publication()
        if validation['errors']:
            fail('migration-preflight', '0.2 publication validation failed: ' +
                 validation['errors'][0]['code'])
        queue.extend(resolve(reader.base, route['href']) for route in reader.manifest.get('routes', []))

    converted = {url: copy.deepcopy(document) for url, document in documents.items()}
    for document in converted.values():
        document['formatVersion'] = '1.0'

    completed = {}
    active = set()

    def convert(url):
        if url in active:
            fail('cycle', 'Descriptor cycle during migration')
        if url in completed:
            return completed[url]
        if url not in converted:
            fail('migration-input', 'Referenced descriptor was not captured')
        active.add(url)
        document = converted[url]
        for link in document.get('catalogs', []):
            child_url = resolve(url, link['href'])
            child_data = convert(child_url)
            link['revision'] = converted[child_url]['revision']
            link['sha256'] = hashlib.sha256(child_data).hexdigest()
        structure(document)
        data = encoded(document)
        completed[url] = data
        active.remove(url)
        return data

    for url in converted:
        convert(url)
    files = dict(payloads)
    for url, data in completed.items():
        files[local_name(root, url)] = data
    return files, local_name(root, entry.as_uri())


def one_line(value):
    return ' '.join(value.split())


def build_export(source):
    """Copy a validated 1.0 publication and derive llms.txt from its inventory."""
    source = Path(source).resolve()
    entry = source / 'ai.json' if source.is_dir() else source
    root = entry.parent
    reader = Reader10(root)
    payloads = {}
    manifests = {}
    inventories = {}
    original_fetch = reader.transport.fetch

    def capture(url, media=None, descriptor=False):
        if urlsplit(url).scheme != 'file':
            fail('export-input', 'Portable export accepts local references only')
        response = original_fetch(url, media, descriptor)
        name = local_name(root, response.url)
        if name in payloads and payloads[name] != response.data:
            fail('revision-mismatch', 'Source changed during preflight')
        payloads[name] = response.data
        if descriptor:
            document = strict_json(response.data)
            if document.get('document') == 'manifest':
                manifests[response.url] = document
        return response

    reader.transport.fetch = capture
    queue = [entry.as_uri()]
    seen = set()
    while queue:
        requested = queue.pop(0)
        if requested in seen:
            continue
        seen.add(requested)
        reader.entry = requested
        reader.discover('manifest')
        reader.inventory()
        validation = reader.publication()
        if validation['errors']:
            fail('export-preflight', '1.0 publication validation failed: ' +
                 validation['errors'][0]['code'])
        inventories[reader.base] = list(reader.report['items'])
        queue.extend(resolve(reader.base, route['href']) for route in reader.manifest.get('routes', []))

    for url, items in inventories.items():
        document = manifests[url]
        folder = Path(local_name(root, url)).parent
        name = (folder / 'llms.txt').as_posix()
        if name in payloads or (root / name).exists():
            fail('export-collision', 'Existing llms.txt requires explicit reconciliation')
        lines = ['# ' + one_line(document['resource']['name']), '',
                 '> ' + one_line(document['resource']['description']), '',
                 '## Documentation', '']
        for item, base in items:
            if item['status'] != 'published':
                continue
            representations = [representation for representation in item['representations']
                               if representation.get('role', 'full') == 'full'
                               and representation['mediaType'] in ('text/markdown', 'text/plain')]
            if not representations:
                fail('export-input', 'Every published item needs a full text representation')
            target = resolve(base, representations[0]['href'])
            relative = Path(os.path.relpath(local_name(root, target), str(folder))).as_posix()
            label = one_line(item['title']).replace('[', '\\[').replace(']', '\\]')
            lines.append(f'- [{label}](<{relative}>): ' + one_line(item['description']))
        payloads[name] = ('\n'.join(lines) + '\n').encode()
    return payloads, local_name(root, entry.as_uri())


def prepare(source, output, mode='migrate'):
    source = Path(source).resolve()
    root = source if source.is_dir() else source.parent
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        fail('output-exists', 'Output must be a new directory')
    if output.resolve().is_relative_to(root) or root.is_relative_to(output.resolve()):
        fail('invalid-output', 'Source and output trees must not overlap')
    if not output.parent.is_dir():
        fail('invalid-output', 'Output parent must already exist')
    files, entry = build(source) if mode == 'migrate' else build_export(source)
    for name in files:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            fail('invalid-output', 'Unsafe generated path')
    report = {'operation': 'migrate-0.2-to-1.0' if mode == 'migrate' else 'joint-export-1.0',
              'status': 'preflight-pass',
              'written': False, 'entry': entry, 'wireVersion': '1.0',
              'semanticChanges': [],
              'files': [{'path': name, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()}
                        for name, data in sorted(files.items())]}
    return files, report


def publish(source, output, apply=False, mode='migrate'):
    files, report = prepare(source, output, mode)
    if not apply:
        return report
    output = Path(output).absolute()
    staging = Path(tempfile.mkdtemp(prefix='.ai-first-1-stage-', dir=output.parent))
    try:
        for name, data in files.items():
            destination = staging / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        candidate = Reader10(staging / report['entry'])
        candidate.discover('manifest')
        candidate.inventory()
        validation = candidate.publication()
        if validation['errors']:
            fail('output-validation', 'Staged 1.0 publication did not validate')
        output.mkdir()
        try:
            for child in staging.iterdir():
                shutil.move(str(child), str(output / child.name))
        except Exception:
            shutil.rmtree(output)
            raise
        report.update(status='written', written=True)
        return report
    finally:
        shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--mode', choices=['migrate', 'export'], default='migrate')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(publish(args.source, args.output, args.apply, args.mode), indent=2))
        return 0
    except Failure as exc:
        print(json.dumps({'status': 'failed', 'error': exc.record(), 'written': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
