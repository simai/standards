"""Read-only OpenAPI/MCP locator validation, never business execution."""
import json
import re
from urllib.parse import unquote, urldefrag, urlsplit
import yaml
from aifirst import fail, strict_json, resolve, METHODS
from aifirst10_core import YAML_MEDIA


class ContractLoader(yaml.SafeLoader):
    # Isolate resolver changes from global PyYAML behavior. Preserve ordinary
    # strings such as operation IDs 'on' and dates instead of YAML 1.1 coercions.
    yaml_implicit_resolvers = {
        k: [(tag, exp) for tag, exp in entries if tag not in
            ('tag:yaml.org,2002:bool', 'tag:yaml.org,2002:timestamp')]
        for k, entries in yaml.SafeLoader.yaml_implicit_resolvers.items()}


ContractLoader.add_implicit_resolver('tag:yaml.org,2002:bool',
                                    re.compile(r'^(?:true|false)$'), list('tf'))


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            fail('invalid-contract', 'YAML object keys must be strings')
        if key in result:
            fail('invalid-contract', 'Duplicate YAML object key')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


ContractLoader.add_constructor('tag:yaml.org,2002:map', mapping)


def parse_contract(data, media):
    if media == 'application/json':
        return strict_json(data)
    if media not in YAML_MEDIA:
        fail('unsupported-media', 'Contract must be JSON or supported YAML')
    try:
        text = data.decode('utf-8')
        if text.startswith('\ufeff'):
            fail('invalid-contract', 'UTF-8 BOM is not accepted')
        depth = 0; events = 0
        for event in yaml.parse(text, Loader=ContractLoader):
            events += 1
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
            if depth > 64 or events > 100000:
                fail('limit-exceeded', 'YAML structural limit exceeded')
        value = yaml.load(text, Loader=ContractLoader)
        budget = 100000
        active = set()
        def bounded(obj, depth=0):
            nonlocal budget
            budget -= 1
            if budget < 0 or depth > 64:
                fail('limit-exceeded', 'Expanded YAML limit exceeded')
            if isinstance(obj, (dict, list)):
                if id(obj) in active:
                    fail('invalid-contract', 'Cyclic YAML alias')
                active.add(id(obj))
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        bounded(k, depth+1); bounded(v, depth+1)
                else:
                    for v in obj: bounded(v, depth+1)
                active.remove(id(obj))
        bounded(value)
        return strict_json(json.dumps(value, allow_nan=False).encode())
    except (yaml.YAMLError, UnicodeError, ValueError, TypeError, RecursionError):
        fail('invalid-contract', 'Unsafe or invalid YAML contract')


def pointer(doc, locator):
    if not isinstance(locator, str) or (locator and not locator.startswith('/')):
        fail('invalid-contract', 'Expected a JSON Pointer')
    result = doc
    if not locator:
        return result
    for raw in locator[1:].split('/'):
        if re.search(r'~(?![01])', raw):
            fail('invalid-contract', 'Invalid JSON Pointer escape')
        key = raw.replace('~1', '/').replace('~0', '~')
        try:
            if isinstance(result, list):
                if not re.fullmatch(r'0|[1-9][0-9]*', key):
                    fail('invalid-contract', 'Invalid array pointer')
                result = result[int(key)]
            else:
                result = result[key]
        except (KeyError, IndexError, TypeError):
            fail('invalid-contract', 'Contract locator does not resolve')
    return result


def validate_contract(transport, item, base):
    cap = item['capability']; c = cap['contract']
    url = resolve(base, c['href'])
    if urlsplit(url).fragment:
        fail('invalid-contract', 'Contract href must not include a fragment')
    response = transport.fetch(url, c['mediaType'])
    result = {'id': item['id'], 'type': c['type'], 'contract': response.url,
              'operation': c['operation'], 'binding': 'not-run',
              'fullContractValidation': 'not-run', 'businessExecution': 'not-run'}
    if c['type'] == 'external':
        transport.fetch(resolve(base, cap['instructions']))
        return result
    doc = parse_contract(response.data, c['mediaType'])
    if c['type'] == 'mcp':
        if not isinstance(doc, dict) or not isinstance(doc.get('tools'), list):
            fail('invalid-contract', 'Expected an MCP tool snapshot')
        matches = [t for t in doc['tools'] if isinstance(t, dict) and t.get('name') == c['operation']]
        if len(matches) != 1 or not isinstance(matches[0].get('inputSchema'), dict):
            fail('invalid-contract', 'MCP locator does not resolve uniquely')
    else:
        if not isinstance(doc, dict) or not re.fullmatch(r'3\.[012]\.[0-9]+', str(doc.get('openapi', ''))):
            fail('invalid-contract', 'Expected OpenAPI 3.0.x, 3.1.x or 3.2.x')
        parts = c['operation'].split('/')
        methods = METHODS | ({'query'} if doc['openapi'].startswith('3.2.') else set())
        additional = (doc['openapi'].startswith('3.2.') and len(parts) == 5
                      and parts[3] == 'additionalOperations'
                      and re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", parts[4])
                      and parts[4].upper() not in {m.upper() for m in methods})
        if parts[:2] != ['', 'paths'] or not (
                len(parts) == 4 and parts[-1] in methods or additional):
            fail('invalid-contract', 'Unsupported OpenAPI operation pointer')
        if not parts[2].startswith('~1'):
            fail('invalid-contract', 'OpenAPI path must start with /')
        path_item = pointer(doc, '/'.join(parts[:3]))
        current = response.url; document = doc; seen = set()
        # Resolve Path Item references without duplicating operation definitions.
        for _ in range(transport.limits.depth+1):
            if not isinstance(path_item, dict):
                fail('invalid-contract', 'Expected a Path Item Object')
            if '$ref' not in path_item:
                break
            if any(k in path_item for k in methods | {'additionalOperations'}):
                fail('invalid-contract', 'Conflicting Path Item ref and local operations')
            ref = resolve(current, path_item['$ref'])
            if ref in seen:
                fail('cycle', 'Path Item reference cycle')
            seen.add(ref)
            target, fragment = urldefrag(ref)
            if target != current:
                fetched = transport.fetch(target)
                mime = fetched.headers.get('content-type', '').split(';')[0].lower().strip()
                if not mime and transport.root is not None:
                    mime = 'application/json' if target.endswith('.json') else 'application/yaml'
                document = parse_contract(fetched.data, mime)
                current = fetched.url
            path_item = pointer(document, unquote(fragment))
        else:
            fail('limit-exceeded', 'Path Item reference depth exceeded')
        operation = pointer(path_item, '/' + '/'.join(parts[3:]))
        if not isinstance(operation, dict):
            fail('invalid-contract', 'Locator target is not an operation')
        if 'responses' in operation:
            responses = operation['responses']
            if not isinstance(responses, dict) or not any(
                    k == 'default' or re.fullmatch(r'[1-5](?:[0-9]{2}|XX)', k) for k in responses):
                fail('invalid-contract', 'Operation has no declared response code')
        elif doc['openapi'].startswith('3.0.'):
            fail('invalid-contract', 'OpenAPI 3.0 operation requires responses')
        result['openapiVersion'] = doc['openapi']
    transport.fetch(resolve(base, cap['instructions']))
    result['binding'] = 'pass'
    return result

