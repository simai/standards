#!/usr/bin/env python3
"""AI First 0.2 reference reader; never calls advertised business operations."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from urllib.parse import urldefrag, urlsplit, urlunsplit
from aifirst import Failure, fail, strict_json, resolve, scope_url, covers, Reader as Reader01
from aifirst02_core import Inventory, structure
from aifirst02_transport import Transport


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if (tag == 'link' and 'describedby' in a.get('rel', '').lower().split()
                and a.get('type', '').lower() == 'application/json'
                and a.get('data-ai-first') == '0.2' and a.get('href')):
            self.targets.append(a['href'])


def split_fields(value, delimiter):
    """Split Link syntax outside quoted strings and angle-delimited URLs."""
    parts = []; start = 0; quoted = False; angled = False; escaped = False
    for i, ch in enumerate(value):
        if escaped:
            escaped = False; continue
        if quoted and ch == '\\':
            escaped = True; continue
        if ch == '"' and not angled:
            quoted = not quoted
        elif not quoted:
            if ch == '<': angled = True
            elif ch == '>': angled = False
            elif ch == delimiter and not angled:
                parts.append(value[start:i].strip()); start = i+1
    parts.append(value[start:].strip())
    return parts


def header_links(value):
    targets = []
    for field in split_fields(value, ','):
        parts = split_fields(field, ';')
        if not parts[0].startswith('<') or not parts[0].endswith('>'):
            continue
        params = {}
        duplicates = set()
        for part in parts[1:]:
            key, sep, val = part.partition('=')
            if not sep: continue
            key = key.strip().lower(); val = val.strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            if key in params: duplicates.add(key)
            params[key] = val
        if ('describedby' in params.get('rel', '').lower().split()
                and params.get('type', '').lower() == 'application/json'
                and params.get('ai-first') == '0.2'):
            if duplicates or 'anchor' in params:
                fail('ambiguous-discovery', 'Ambiguous or alternate-context Link declaration')
            targets.append(parts[0][1:-1])
    return targets


class Reader:
    def __init__(self, entry, **policy):
        self.transport = Transport(entry, **policy)
        self.entry = self.transport.entry
        self.manifest = None; self.base = None; self.report = None
        self.mode = 'offline' if self.transport.root else 'online'

    def document(self, location, kind):
        response = self.transport.fetch(location, 'application/json', descriptor=True)
        return structure(strict_json(response.data), kind), response.url

    def discover(self, mode='root'):
        page = None
        if mode == 'manifest':
            location = self.entry
        elif mode == 'root':
            if not self.entry.endswith('/'):
                fail('invalid-entry', 'Root entry must end in /')
            location = resolve(self.entry, 'ai.json'); page = self.entry
        elif mode == 'page':
            if self.mode == 'offline':
                fail('invalid-entry', 'Page discovery requires HTTP(S)')
            response = self.transport.fetch(self.entry, 'text/html', descriptor=True)
            page = response.url
            parser = PageLinks()
            try:
                parser.feed(response.data.decode('utf-8'))
            except UnicodeError:
                fail('invalid-text', 'Page is not UTF-8')
            links = parser.targets + header_links(response.headers.get('link', ''))
            targets = {urldefrag(resolve(page, link))[0] for link in links}
            if len(targets) > 1:
                fail('ambiguous-discovery', 'Conflicting manifest declarations')
            p = urlsplit(page)
            location = next(iter(targets)) if targets else urlunsplit((p.scheme, p.netloc, '/ai.json', '', ''))
        else:
            fail('invalid-entry', 'Unknown discovery mode')
        seen = set(); expected_scope = None
        for _ in range(self.transport.limits.depth+1):
            manifest, final = self.document(location, 'manifest')
            if final in seen:
                fail('cycle', 'Manifest route cycle')
            seen.add(final)
            scope = scope_url(final, manifest['resource']['scope'])
            if expected_scope is not None and scope != expected_scope:
                fail('scope-mismatch', 'Routed manifest has a different scope')
            routes = Reader01.routes(self, manifest, final, scope)
            if page:
                if not covers(scope, page):
                    fail('scope-mismatch', 'Manifest does not cover the entry page')
                matches = [r for r in routes if covers(r[0], page)]
                if matches:
                    expected_scope, location = max(matches, key=lambda r: len(urlsplit(r[0]).path))
                    continue
            self.manifest = manifest; self.base = final
            return manifest
        fail('limit-exceeded', 'Manifest route depth exceeded')

    def inventory(self, query=None):
        if self.manifest is None:
            fail('invalid-entry', 'Discover before reading inventory')
        def fetch(url):
            response = self.transport.fetch(url, 'application/json', descriptor=True)
            return response.data, response.url
        limits = self.transport.limits
        self.report = Inventory(fetch, resolve, max_documents=limits.documents,
                                max_items=limits.items, max_depth=limits.depth).walk(
                                    self.manifest, self.base, query)
        return self.report

    def select(self, *, item_id=None, query='', language=None, fallback_languages=(),
               product=None, version=None, kind=None, translation_of=None):
        if self.report is None:
            fail('invalid-entry', 'Read inventory before selection')
        if fallback_languages and not language:
            fail('invalid-policy', 'Language fallback requires a requested language')
        if fallback_languages and item_id:
            fail('invalid-policy', 'An explicit item ID cannot fall back to another ID')
        found = []
        for item, base in self.report['items']:
            a = item.get('appliesTo', {})
            if item['status'] != 'published': continue
            if item_id and item['id'] != item_id: continue
            if translation_of and item.get('translationOf') != translation_of: continue
            if kind and item['kind'] != kind: continue
            if product and product != a.get('product'): continue
            if version and version not in a.get('versions', []): continue
            if not all(t in (item['title']+' '+item['description']).lower() for t in query.lower().split()): continue
            found.append((item, base))
        if not language:
            return found
        exact = [(i, b) for i, b in found if i['language'].lower() == language.lower()]
        if exact or not fallback_languages:
            return exact
        # Fallback cannot establish translation equivalence from a title query.
        if not translation_of:
            fail('invalid-policy', 'Fallback requires a specific translationOf identity')
        for alternative in fallback_languages:
            selected = [(i, b) for i, b in found if i['language'].lower() == alternative.lower()]
            if selected: return selected
        return []

    def material(self, item, base, *, requested_language=None):
        failures = []
        for rep in item['representations']:
            if rep.get('role', 'full') != 'full': continue
            if rep['mediaType'] not in ('text/plain', 'text/markdown', 'text/html', 'application/json'): continue
            try:
                response = self.transport.fetch(resolve(base, rep['href']), rep['mediaType'])
                digest = hashlib.sha256(response.data).hexdigest()
                if rep.get('sha256', digest) != digest:
                    fail('digest-mismatch', 'Material differs from declared digest')
                try:
                    text = response.data.decode('utf-8')
                except UnicodeError:
                    fail('invalid-text', 'Representation is not UTF-8')
                return {'id': item['id'], 'revision': item['revision'],
                        'publicationRevision': self.manifest['revision'],
                        'source': resolve(base, item['source']), 'representation': response.url,
                        'mediaType': rep['mediaType'], 'sha256': digest, 'text': text,
                        'requestedLanguage': requested_language, 'language': item['language'],
                        'languageFallback': bool(requested_language and requested_language.lower() != item['language'].lower()),
                        'completeness': self.report['completeness'],
                        'omittedCatalogs': self.report['omittedCatalogs'], 'errors': self.report['errors'],
                        'warnings': failures, 'mode': self.mode, 'cache': response.cache,
                        'freshness': 'revalidated' if response.cache == 'revalidated' else 'unknown'}
            except Failure as exc:
                failures.append(exc.record())
                if exc.code == 'access-denied':
                    raise
        fail(failures[0]['code'] if failures else 'unsupported-media', 'No readable full representation')


    def publication(self):
        from aifirst02_contracts import validate_contract
        if self.report is None:
            fail('invalid-entry', 'Read inventory before validation')
        if self.report['omittedCatalogs']:
            fail('invalid-policy', 'Publication validation requires full traversal')
        errors = list(self.report['errors']); contracts = []
        for item, base in self.report['items']:
            for rep in item['representations']:
                try:
                    response = self.transport.fetch(resolve(base, rep['href']), rep['mediaType'])
                    digest = hashlib.sha256(response.data).hexdigest()
                    if rep.get('sha256', digest) != digest:
                        fail('digest-mismatch', 'Representation differs from declared digest')
                    if rep['mediaType'].startswith('text/') or rep['mediaType'] == 'application/json':
                        try: response.data.decode('utf-8')
                        except UnicodeError: fail('invalid-text', 'Text is not UTF-8')
                except Failure as exc:
                    errors.append(dict(exc.record(), item=item['id'], role='representation'))
            try:
                self.transport.fetch(resolve(base, item['source']))
            except Failure as exc:
                errors.append(dict(exc.record(), item=item['id'], role='source'))
            if item['kind'] == 'capability':
                try:
                    contracts.append(validate_contract(self.transport, item, base))
                except Failure as exc:
                    errors.append(dict(exc.record(), item=item['id'], role='contract'))
        scope = scope_url(self.base, self.manifest['resource']['scope'])
        for child_scope, href in Reader01.routes(self, self.manifest, self.base, scope):
            try:
                child, final = self.document(href, 'manifest')
                if scope_url(final, child['resource']['scope']) != child_scope:
                    fail('scope-mismatch', 'Child manifest scope differs from route')
            except Failure as exc:
                errors.append(dict(exc.record(), role='route'))
        return {'publication': 'fail' if errors else 'pass',
                'validation': 'materials-contract-locators-and-immediate-routes',
                'completeness': self.report['completeness'],
                'items': len(self.report['items']), 'errors': errors,
                'contractLocators': contracts, 'businessExecution': 'not-run',
                'routedPublicationInventories': 'not-run', 'mode': self.mode}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'read', 'validate'])
    parser.add_argument('entry')
    parser.add_argument('--mode', choices=['root', 'manifest', 'page'], default='root')
    parser.add_argument('--allow-loopback', action='store_true')
    parser.add_argument('--allow-origin', action='append', default=[])
    parser.add_argument('--allow-network', action='append', default=[])
    parser.add_argument('--ca-file')
    for name in ('id', 'query', 'language', 'product', 'version', 'kind', 'translation-of'):
        parser.add_argument('--'+name)
    parser.add_argument('--fallback-language', action='append', default=[])
    parser.add_argument('--full', action='store_true', help='Traverse all catalogs regardless of selectors')
    args = parser.parse_args(argv)
    try:
        reader = Reader(args.entry, allow_loopback=args.allow_loopback,
                        allow_origins=args.allow_origin, allow_networks=args.allow_network,
                        ca_file=args.ca_file)
        reader.discover(args.mode)
        selection = {k: v for k, v in {
            'ids': [args.id] if args.id else [],
            'languages': [args.language, *args.fallback_language] if args.language else [],
            'products': [args.product] if args.product else [],
            'versions': [args.version] if args.version else [],
            'kinds': [args.kind] if args.kind else []}.items() if v}
        report = reader.inventory(None if args.full or args.command == 'validate' else selection)
        found = reader.select(item_id=args.id, query=args.query or '', language=args.language,
                              fallback_languages=args.fallback_language, product=args.product,
                              version=args.version, kind=args.kind, translation_of=args.translation_of)
        if args.command == 'read':
            if not found:
                fail('indeterminate' if report['errors'] else 'no-match', 'No material selected')
            if len(found) != 1:
                fail('ambiguous-selection', 'Selection requires one item')
            result = reader.material(*found[0], requested_language=args.language)
        elif args.command == 'validate':
            result = reader.publication()
        else:
            result = dict(report, items=[i for i, _ in found])
        result['retrieved'] = reader.transport.records
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('errors') else 0
    except Failure as exc:
        print(json.dumps({'error': exc.record()}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
