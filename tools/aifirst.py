#!/usr/bin/env python3
"""AI First 0.1 reference reader. Never executes advertised capabilities."""
from __future__ import annotations
import argparse
import hashlib
import http.client
import ipaddress
import json
import socket
import ssl
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlsplit, urlunsplit
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {'core', 'knowledge', 'capability'}
METHODS = {'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'}

class Failure(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
    def record(self):
        return {'code': self.code, 'message': str(self)}

def fail(code, message):
    raise Failure(code, message)

def strict_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                fail('invalid-json', 'Duplicate JSON object key')
            result[key] = value
        return result
    def constant(_):
        fail('invalid-json', 'Non-finite number')
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=constant)
        def walk(obj, depth=0):
            if depth > 64:
                fail('limit-exceeded', 'JSON nesting exceeds 64')
            if isinstance(obj, str):
                obj.encode('utf-8')
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    walk(k, depth+1); walk(v, depth+1)
            elif isinstance(obj, list):
                for v in obj: walk(v, depth+1)
            elif isinstance(obj, float):
                import math
                if not math.isfinite(obj): fail('invalid-json', 'Non-finite number')
        walk(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        fail('invalid-json', type(exc).__name__)

def structure(value, expected=None):
    if not isinstance(value, dict) or value.get('format') != 'ai-first':
        fail('unknown-format', 'Expected an AI First object')
    if value.get('formatVersion') != '0.1':
        fail('unsupported-version', 'Reader supports wire version 0.1')
    kind = value.get('document')
    if kind not in ('manifest', 'catalog') or (expected and kind != expected):
        fail('invalid-structure', 'Unexpected document kind')
    schema = json.loads((ROOT / 'schemas' / (kind+'.schema.json')).read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        e = errors[0]
        fail('invalid-structure', 'Schema violation at /'+'/'.join(map(str, e.path)))
    if set(value.get('requires', [])) - PROFILES:
        fail('unsupported-profile', 'Document requires an unsupported profile')
    for item in value.get('items', []):
        if not any(r.get('role', 'full') == 'full' for r in item['representations']):
            fail('invalid-structure', 'Item requires a full representation')
        if any(r.get('language', item['language']).lower() != item['language'].lower()
               for r in item['representations']):
            fail('invalid-structure', 'Translation requires a separate item')
        if item['kind'] == 'capability':
            c = item['capability']['contract']
            if c['type'] in ('openapi', 'mcp') and c['mediaType'] != 'application/json':
                fail('invalid-contract', 'JSON contract mediaType required')
            if c['type'] == 'external' and not c.get('description'):
                fail('invalid-contract', 'External locator semantics must be explained')
    return value

def origin(url):
    p = urlsplit(url)
    return (p.scheme, p.hostname, p.port or (443 if p.scheme == 'https' else 80))

def resolve(base, href):
    if any(ord(c) <= 32 or ord(c) == 127 for c in href) or '\\' in href or href.startswith('//'):
        fail('access-blocked', 'Unsafe link spelling')
    p = urlsplit(href)
    if p.username is not None or p.password is not None:
        fail('access-blocked', 'Credentials in links are forbidden')
    return urljoin(base, href)

def scope_url(base, href):
    result = resolve(base, href)
    p = urlsplit(result)
    if not p.path.endswith('/') or p.query or p.fragment or p.scheme not in ('file','https','http'):
        fail('invalid-scope', 'Scope must be a directory without query or fragment')
    decoded = unquote(p.path)
    if decoded != p.path and ('/' in unquote(p.path.replace('/', '')) or '\\' in decoded
                              or any(part in ('.', '..') for part in decoded.split('/'))):
        fail('invalid-scope', 'Encoded path separators or dot segments are ambiguous')
    return result

def covers(scope, target):
    a, b = urlsplit(scope), urlsplit(target)
    return origin(scope) == origin(target) and b.path.startswith(a.path)

class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if (tag == 'link' and 'alternate' in a.get('rel','').lower().split()
            and a.get('type','').lower() == 'application/json'
            and a.get('data-ai-first') == '0.1' and a.get('href')):
            self.targets.append(a['href'])

class PinnedTLS(http.client.HTTPSConnection):
    """Connect only to a validated IP while retaining hostname TLS verification."""
    def __init__(self, host, port, address, timeout):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self.address = address
    def connect(self):
        raw = socket.create_connection((self.address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close(); raise

@dataclass
class Limits:
    descriptor_bytes: int = 256*1024
    material_bytes: int = 8*1024*1024
    total_bytes: int = 32*1024*1024
    documents: int = 64
    depth: int = 8
    items: int = 10000
    timeout: float = 10

class Reader:
    def __init__(self, entry, *, allow_loopback=False, allow_origins=(), limits=None):
        self.limits = limits or Limits()
        self.allow_loopback = allow_loopback
        self.total = 0; self.documents = 0
        self.items = []; self.errors = []; self.visited = set(); self.ids = set()
        self.records = []; self.manifest = None; self.base = None
        self.root = None
        if urlsplit(str(entry)).scheme in ('https', 'http'):
            self.entry = str(entry)
            self.allowed = {origin(self.entry)} | {origin(u) for u in allow_origins}
        else:
            path = Path(entry).resolve()
            self.root = path if path.is_dir() else path.parent
            self.entry = path.as_uri() + ('/' if path.is_dir() else '')
            self.allowed = {origin(u) for u in allow_origins}
        self.mode = 'offline' if self.root is not None else 'online'

    def fetch(self, url, media=None, descriptor=False):
        url, _ = urldefrag(url)
        p = urlsplit(url)
        if p.username is not None or p.password is not None or '\\' in url or any(ord(c)<=32 or ord(c)==127 for c in url):
            fail('access-blocked', 'Unsafe retrieval URL')
        cap = self.limits.descriptor_bytes if descriptor else self.limits.material_bytes
        if descriptor:
            self.documents += 1
            if self.documents > self.limits.documents: fail('limit-exceeded', 'Descriptor count exceeded')
        handle = None; connection = None
        try:
            if p.scheme == 'file':
                if self.root is None or p.netloc or p.query:
                    fail('access-blocked', 'Local read is not authorized')
                path = Path(unquote(p.path)).resolve()
                if not path.is_relative_to(self.root): fail('access-blocked', 'Path leaves authorized root')
                handle = path.open('rb')
            elif p.scheme in ('https','http'):
                if origin(url) not in self.allowed: fail('access-blocked', 'Origin is not authorized')
                host = p.hostname
                if not host: fail('access-blocked','Missing host')
                port = p.port or (443 if p.scheme == 'https' else 80)
                addresses = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)))
                if not addresses: fail('unavailable', 'Host did not resolve')
                for address in addresses:
                    ip = ipaddress.ip_address(address)
                    if not ip.is_global and not (self.allow_loopback and ip.is_loopback):
                        fail('access-blocked', 'Non-public network destination')
                if p.scheme == 'http':
                    if not self.allow_loopback or not all(ipaddress.ip_address(a).is_loopback for a in addresses):
                        fail('access-blocked', 'HTTP allowed only for explicit loopback development')
                    connection = http.client.HTTPConnection(addresses[0],port,timeout=self.limits.timeout)
                else:
                    connection = PinnedTLS(host,port,addresses[0],self.limits.timeout)
                path = urlunsplit(('', '', p.path or '/', p.query, ''))
                connection.request('GET',path,headers={'Host':p.netloc,'Accept':media or '*/*','Accept-Encoding':'identity'})
                handle = connection.getresponse()
                if handle.status in (401,403): fail('access-denied', 'Resource requires access')
                if handle.status in (404,410): fail('not-found','Resource does not exist')
                if 300 <= handle.status < 400: fail('redirect-blocked','Reference reader does not follow redirects')
                if handle.status != 200: fail('unavailable', 'HTTP status '+str(handle.status))
                if handle.getheader('Content-Encoding', 'identity').lower() != 'identity':
                    fail('unsupported-encoding', 'Only identity encoding is supported')
                actual = handle.getheader('Content-Type','').split(';')[0].strip().lower()
                if media and actual != media: fail('media-mismatch', 'Response MIME type differs from declaration')
            else:
                fail('access-blocked','Unsupported retrieval scheme')
            data = handle.read(min(cap, max(0,self.limits.total_bytes-self.total))+1)
            self.total += len(data)
            if len(data)>cap or self.total>self.limits.total_bytes: fail('limit-exceeded','Byte limit exceeded')
            self.records.append({'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
            return data
        except FileNotFoundError: fail('not-found','Local resource does not exist')
        except PermissionError: fail('access-denied','Local read denied')
        except (OSError, ValueError, http.client.HTTPException) as exc:
            fail('unavailable', type(exc).__name__)
        finally:
            if handle is not None: handle.close()
            if connection is not None: connection.close()

    def document(self,url,expected):
        return structure(strict_json(self.fetch(url,'application/json',True)),expected)

    def discover(self, mode='root'):
        target_page = None
        if mode == 'manifest': location = self.entry
        elif mode == 'root':
            if not self.entry.endswith('/'): fail('invalid-entry','Root URL must end in /; use --mode manifest for a file')
            location = resolve(self.entry,'ai.json')
            target_page = self.entry
        else:
            if self.root is not None: fail('invalid-entry','Page discovery requires HTTP(S)')
            target_page = self.entry
            parser = PageLinks()
            try: parser.feed(self.fetch(self.entry,'text/html',True).decode('utf-8'))
            except UnicodeError: fail('invalid-text','Page is not UTF-8')
            targets = set(resolve(self.entry,t) for t in parser.targets)
            if len(targets)>1: fail('ambiguous-discovery','Multiple marked manifest links')
            p = urlsplit(self.entry)
            location = next(iter(targets)) if targets else urlunsplit((p.scheme,p.netloc,'/ai.json','',''))
        seen=set()
        for _ in range(self.limits.depth+1):
            if location in seen: fail('cycle','Manifest route cycle')
            seen.add(location)
            manifest = self.document(location,'manifest')
            scope = scope_url(location,manifest['resource']['scope'])
            routes = self.routes(manifest,location,scope)
            if target_page:
                if not covers(scope,target_page): fail('scope-mismatch','Manifest does not cover page')
                matches=[r for r in routes if covers(r[0],target_page)]
                if matches:
                    matched=max(matches,key=lambda r:len(urlsplit(r[0]).path))
                    child=self.document(matched[1],'manifest')
                    if scope_url(matched[1],child['resource']['scope']) != matched[0]:
                        fail('scope-mismatch','Child scope differs from route')
                    location=matched[1]; continue
            self.manifest=manifest; self.base=location
            return manifest
        fail('limit-exceeded','Route depth exceeded')

    def routes(self,manifest,base,scope):
        result=[]; scopes=set()
        for r in manifest.get('routes',[]):
            child=scope_url(base,r['scope'])
            if child==scope or not covers(scope,child): fail('invalid-scope','Child scope must be inside parent')
            if child in scopes: fail('ambiguous-discovery','Duplicate route scope')
            scopes.add(child); result.append((child,resolve(base,r['href'])))
        return result

    def inventory(self):
        if self.manifest is None: fail('invalid-entry','Discover a manifest first')
        self.items=[]; self.errors=[]; self.visited=set(); self.ids=set()
        def visit(doc,base,stack,depth):
            if depth>self.limits.depth: fail('limit-exceeded','Catalog depth exceeded')
            if base in stack: fail('cycle','Catalog cycle')
            if base in self.visited: return
            self.visited.add(base)
            for item in doc.get('items',[]):
                if item['id'] in self.ids: fail('duplicate-id','Item IDs must be unique')
                self.ids.add(item['id'])
                if len(self.ids)>self.limits.items: fail('limit-exceeded','Item count exceeded')
                self.items.append((item,base))
            for link in doc.get('catalogs',[]):
                try:
                    url=resolve(base,link['href'])
                    if url in stack or url==base: fail('cycle','Catalog cycle')
                    if url in self.visited: continue
                    if depth+1>self.limits.depth: fail('limit-exceeded','Catalog depth exceeded')
                    child=self.document(url,'catalog')
                    if child['revision'] != self.manifest['revision'] or child['resourceId'] != self.manifest['resource']['id']:
                        fail('revision-mismatch','Catalog snapshot or identity mismatch')
                    visit(child,url,stack|{base},depth+1)
                except Failure as exc: self.errors.append(exc.record())
        visit(self.manifest,self.base,set(),0)
        return self.items

    def select(self,query='',product=None,version=None,language=None,item_id=None):
        found=[]
        for item,base in self.items:
            a=item.get('appliesTo',{})
            if item['status'] != 'published': continue
            if item_id and item['id'] != item_id: continue
            if product and a.get('product') != product: continue
            if version and version not in a.get('versions',[]): continue
            if language and item['language'].lower()!=language.lower(): continue
            text=(item['title']+' '+item['description']).lower()
            if not all(term in text for term in query.lower().split()): continue
            found.append((item,base))
        return found

    def material(self,item,base):
        errors=[]
        for rep in item['representations']:
            if rep.get('role','full')!='full': continue
            if rep['mediaType'] not in ('text/markdown','text/plain','text/html','application/json'): continue
            try:
                url=resolve(base,rep['href'])
                data=self.fetch(url,rep['mediaType'])
                digest=hashlib.sha256(data).hexdigest()
                if rep.get('sha256',digest)!=digest: fail('digest-mismatch','Representation bytes changed')
                try: text=data.decode('utf-8')
                except UnicodeError: fail('invalid-text','Representation is not UTF-8')
                return {'id':item['id'],'revision':item['revision'],'publicationRevision':self.manifest['revision'],
                        'source':resolve(base,item['source']),'representation':url,'mediaType':rep['mediaType'],
                        'sha256':digest,'text':text,'warnings':errors,'mode':self.mode,'freshness':'unknown'}
            except Failure as exc: errors.append(exc.record())
        fail(errors[0]['code'] if errors else 'unsupported-media','No readable full representation')

    def contract(self,item,base):
        cap=item['capability']; c=cap['contract']
        url=resolve(base,c['href'])
        if urlsplit(url).fragment: fail('invalid-contract','Contract href must not have fragment')
        data=self.fetch(url,c['mediaType'])
        if c['type']=='external':
            self.fetch(resolve(base,cap['instructions']))
            return 'not-run'
        doc=strict_json(data)
        if c['type']=='openapi':
            if not isinstance(doc,dict) or not str(doc.get('openapi','')).startswith(('3.1.','3.2.')):
                fail('invalid-contract','Expected OpenAPI 3.1.x or 3.2.x')
            parts=c['operation'].split('/')
            if len(parts)!=4 or parts[0]!='' or parts[1]!='paths' or parts[-1] not in METHODS:
                fail('invalid-contract','Operation must point to /paths/{path}/{method}')
            obj=doc
            try:
                for part in parts[1:]: obj=obj[part.replace('~1','/').replace('~0','~')]
            except (KeyError,TypeError): fail('invalid-contract','Operation does not resolve')
            if not isinstance(obj,dict) or 'responses' not in obj:
                fail('invalid-contract','Target is not an Operation Object')
        else:
            if not isinstance(doc,dict): fail('invalid-contract','Expected a tool snapshot')
            matches=[t for t in doc.get('tools',[]) if isinstance(t,dict) and t.get('name')==c['operation']]
            if len(matches)!=1 or not isinstance(matches[0].get('inputSchema'),dict):
                fail('invalid-contract','Tool snapshot locator does not resolve uniquely')
        self.fetch(resolve(base,cap['instructions']))
        return 'pass'

    def publication(self):
        errors=list(self.errors); contracts=[]
        for item,base in self.items:
            for rep in item['representations']:
                try:
                    data=self.fetch(resolve(base,rep['href']),rep['mediaType'])
                    if rep.get('sha256',hashlib.sha256(data).hexdigest()) != hashlib.sha256(data).hexdigest():
                        fail('digest-mismatch','Representation bytes changed')
                except Failure as exc: errors.append(dict(exc.record(),item=item['id']))
            try: self.fetch(resolve(base,item['source']))
            except Failure as exc: errors.append(dict(exc.record(),item=item['id'],role='source'))
            if item['kind']=='capability':
                try: contracts.append({'id':item['id'],'status':self.contract(item,base)})
                except Failure as exc: errors.append(dict(exc.record(),item=item['id']))
        # Check immediate routed manifests; their inventories are separate publications.
        for scope,url in self.routes(self.manifest,self.base,scope_url(self.base,self.manifest['resource']['scope'])):
            try:
                child=self.document(url,'manifest')
                if scope_url(url,child['resource']['scope'])!=scope: fail('scope-mismatch','Child scope differs from route')
            except Failure as exc: errors.append(exc.record())
        structural_codes={'invalid-json','invalid-structure','unknown-format','unsupported-version','unsupported-profile'}
        return {'structure':'fail' if any(e['code'] in structural_codes for e in errors) else 'pass',
                'publication':'fail' if errors else 'pass',
                'runtimeConformance':'not-run','contractLocators':contracts,'errors':errors,
                'items':len(self.items),'mode':self.mode,'freshness':'unknown','retrieved':self.records}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['validate','list','read'])
    p.add_argument('entry')
    p.add_argument('--mode',choices=['root','manifest','page'],default='root')
    p.add_argument('--structure-only',action='store_true')
    p.add_argument('--allow-loopback',action='store_true')
    p.add_argument('--allow-origin',action='append',default=[])
    p.add_argument('--query',default=''); p.add_argument('--product'); p.add_argument('--version')
    p.add_argument('--language'); p.add_argument('--id')
    args=p.parse_args(argv)
    try:
        r=Reader(args.entry,allow_loopback=args.allow_loopback,allow_origins=args.allow_origin)
        if args.structure_only:
            if args.command!='validate' or args.mode!='manifest':
                fail('invalid-entry','--structure-only requires validate --mode manifest')
            d=r.document(r.entry,None)
            result={'structure':'pass','publication':'not-run','runtimeConformance':'not-run','document':d['document']}
        else:
            r.discover(args.mode); r.inventory()
            if args.command=='validate': result=r.publication()
            else:
                selected=r.select(args.query,args.product,args.version,args.language,args.id)
                if args.command=='read':
                    if r.errors: fail('partial-inventory','Cannot select from incomplete inventory')
                    if not selected: fail('no-match','No published item matches all filters')
                    if len(selected)>1: fail('ambiguous-selection','Select an exact item ID or add filters')
                    result=r.material(*selected[0])
                else:
                    result={'status':'partial' if r.errors else 'complete','items':[i for i,b in selected],'errors':r.errors}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get('errors') else 0
    except Failure as exc:
        print(json.dumps({'status':'fail','errors':[exc.record()]},indent=2)); return 1
    except (ValueError,RecursionError) as exc:
        print(json.dumps({'status':'fail','errors':[{'code':'invalid-entry','message':type(exc).__name__}]})); return 1

if __name__=='__main__': sys.exit(main())
