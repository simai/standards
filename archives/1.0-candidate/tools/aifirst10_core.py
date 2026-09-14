"""AI First 1.0 structural validation and selective catalog semantics.

Separate wire handler: importing this module never changes 0.1 validation.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from aifirst import Failure, fail, strict_json

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {'core', 'knowledge', 'capability', 'selective-catalogs',
            'translations', 'protected-reading'}
YAML_MEDIA = {'application/yaml', 'text/yaml', 'application/x-yaml'}
SCHEMAS = {kind: Draft202012Validator(json.loads(
    (ROOT / 'schemas' / '1.0' / (kind + '.schema.json')).read_text()))
    for kind in ('manifest', 'catalog')}


def structure(value, expected=None):
    if not isinstance(value, dict) or value.get('format') != 'ai-first':
        fail('unknown-format', 'Expected an AI First object')
    if value.get('formatVersion') != '1.0':
        fail('unsupported-version', 'This handler supports wire version 1.0')
    kind = value.get('document')
    if kind not in SCHEMAS or (expected and kind != expected):
        fail('invalid-structure', 'Unexpected document kind')
    errors = sorted(SCHEMAS[kind].iter_errors(value), key=lambda e: str(e.path))
    if errors:
        fail('invalid-structure', 'Schema violation at /' +
             '/'.join(map(str, errors[0].path)))
    required = set(value.get('requires', []))
    if required - PROFILES:
        fail('unsupported-profile', 'Unsupported required profile')
    used = set()
    if 'access' in value:
        used.add('protected-reading')
    for link in value.get('catalogs', []):
        if 'select' in link:
            used.add('selective-catalogs')
    ids = set()
    for item in value.get('items', []):
        if item['id'] in ids:
            fail('duplicate-id', 'Item IDs must be unique')
        ids.add(item['id'])
        if 'translationOf' in item:
            used.add('translations')
        if not any(r.get('role', 'full') == 'full' for r in item['representations']):
            fail('invalid-structure', 'Item requires a full representation')
        if any(r.get('language', item['language']).lower() != item['language'].lower()
               for r in item['representations']):
            fail('invalid-structure', 'Translations require separate items')
        if item['kind'] == 'capability':
            c = item['capability']['contract']
            allowed = {'application/json'} | (YAML_MEDIA if c['type'] == 'openapi' else set())
            if c['type'] != 'external' and c['mediaType'] not in allowed:
                fail('invalid-contract', 'Unsupported contract media type')
            if c['type'] == 'external' and not c.get('description'):
                fail('invalid-contract', 'External locator semantics must be explained')
    if used - required:
        fail('missing-profile', 'Used profile must appear in requires')
    return value


def matches_selector(item, selector):
    """Check an observed item against an ancestor's declared coverage bound."""
    applicability = item.get('appliesTo', {})
    values = {'ids': [item['id']], 'languages': [item['language']],
              'products': [applicability['product']] if 'product' in applicability else [],
              'versions': applicability.get('versions', []), 'kinds': [item['kind']]}
    for key, bound in selector.items():
        actual = values[key]
        if key == 'languages':
            actual = [s.lower() for s in actual]
            bound = [s.lower() for s in bound]
        if not actual or not set(actual).issubset(bound):
            return False
    return True


def can_skip(selector, query):
    """Only indexed, explicitly constrained dimensions can prove disjointness."""
    for key, bound in selector.items():
        requested = query.get(key)
        if not requested:
            continue
        if key == 'languages':
            bound = [s.lower() for s in bound]
            requested = [s.lower() for s in requested]
        if not set(bound).intersection(requested):
            return True
    return False


def check_pin(link, child, data, resource_id):
    if child['resourceId'] != resource_id:
        fail('resource-mismatch', 'Catalog belongs to another resource')
    if 'revision' in link and link['revision'] != child['revision']:
        fail('revision-mismatch', 'Catalog revision differs from parent pin')
    if 'sha256' in link and link['sha256'] != hashlib.sha256(data).hexdigest():
        fail('digest-mismatch', 'Catalog bytes differ from parent pin')


class Inventory:
    """Bounded traversal with an injected fetcher returning (bytes, final_url).

    Transport validates trust separately. Cached nodes still check all incoming
    pins and bounds. Omissions and failed branches stay visible to the caller.
    """
    def __init__(self, fetch_document, resolve, *, max_documents=64,
                 max_items=10000, max_depth=8):
        self.fetch_document = fetch_document
        self.resolve = resolve
        self.max_documents = max_documents
        self.max_items = max_items
        self.max_depth = max_depth

    def walk(self, manifest, base, query=None):
        structure(manifest, 'manifest')
        query = query or {}
        items = []; errors = []; omitted = []; cache = {}; ids = set()
        observed = {}; final_bytes = {}; requests = 0
        resource_id = manifest['resource']['id']

        def visit(doc, url, stack, bounds, depth):
            nonlocal requests
            if depth > self.max_depth:
                fail('limit-exceeded', 'Catalog depth exceeded')
            if url in stack:
                fail('cycle', 'Catalog cycle')
            # Rechecking a shared subtree must include all ancestor bounds.
            if url in observed:
                for item in observed[url]:
                    if not all(matches_selector(item, b) for b in bounds):
                        fail('selector-mismatch', 'Catalog violates declared coverage')
                return observed[url]
            subtree = []
            for item in doc.get('items', []):
                if not all(matches_selector(item, b) for b in bounds):
                    fail('selector-mismatch', 'Catalog violates declared coverage')
            for item in doc.get('items', []):
                if item['id'] in ids:
                    fail('duplicate-id', 'Different catalogs define the same item ID')
                if len(ids) >= self.max_items:
                    fail('limit-exceeded', 'Item count exceeded')
                ids.add(item['id']); items.append((item, url)); subtree.append(item)
            for link in doc.get('catalogs', []):
                target = self.resolve(url, link['href'])
                if can_skip(link.get('select', {}), query):
                    omitted.append(target)
                    continue
                try:
                    if depth + 1 > self.max_depth:
                        fail('limit-exceeded', 'Catalog depth exceeded')
                    if target in stack or target == url:
                        fail('cycle', 'Catalog cycle')
                    if target not in cache:
                        if requests >= self.max_documents:
                            fail('limit-exceeded', 'Catalog request count exceeded')
                        requests += 1
                        data, final = self.fetch_document(target)
                        child = structure(strict_json(data), 'catalog')
                        if final in final_bytes and final_bytes[final] != data:
                            fail('revision-mismatch', 'Same catalog URL returned different bytes')
                        final_bytes[final] = data
                        cache[target] = (child, data, final)
                    child, data, final = cache[target]
                    check_pin(link, child, data, resource_id)
                    subtree.extend(visit(child, final, stack | {url},
                                         bounds + [link.get('select', {})], depth + 1))
                except Failure as exc:
                    # Duplicate identity affects selection everywhere, not just
                    # a failed branch. Keep this a hard failure.
                    if exc.code == 'duplicate-id':
                        raise
                    errors.append(dict(exc.record(), catalog=target))
            observed[url] = subtree
            return subtree

        visit(manifest, base, set(), [], 0)
        return {'items': items, 'errors': errors, 'omittedCatalogs': omitted,
                'completeness': 'partial' if errors else ('targeted' if omitted else 'complete'),
                'catalogRequests': requests}

