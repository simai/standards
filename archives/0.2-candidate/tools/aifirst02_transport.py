"""Bounded GET transport for AI First 0.2. No operation execution or OAuth flow."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import http.client
import ipaddress
from pathlib import Path
import socket
import ssl
import time
from urllib.parse import unquote, urldefrag, urlsplit, urlunsplit
import zlib
from aifirst import Failure, Limits, fail, origin, resolve


@dataclass
class Response:
    data: bytes
    url: str
    headers: dict
    cache: str = 'none'


class TLSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, address, timeout, context):
        super().__init__(host, port, timeout=timeout, context=context)
        self.address = address

    def connect(self):
        raw = None
        last_error = None
        deadline = time.monotonic() + self.timeout
        for address in self.address:
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Connect deadline exceeded')
                raw = socket.create_connection((address, self.port), remaining)
                break
            except OSError as exc:
                last_error = exc
        if raw is None:
            raise last_error or OSError('No validated address')
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


class Transport:
    def __init__(self, entry, *, limits=None, allow_origins=(), allow_networks=(),
                 allow_loopback=False, ca_file=None, credential_provider=None,
                 credential_scopes=(), principal=None, max_redirects=5):
        self.limits = limits or Limits()
        p = urlsplit(str(entry))
        self.root = None
        if p.scheme in ('http', 'https'):
            self.entry = resolve(str(entry), str(entry))
        else:
            path = Path(entry).resolve()
            self.root = path if path.is_dir() else path.parent
            self.entry = path.as_uri() + ('/' if path.is_dir() else '')
        self.allowed = {origin(self.entry)} | {origin(u) for u in allow_origins}
        self.networks = [ipaddress.ip_network(n, strict=True) for n in allow_networks]
        self.allow_loopback = allow_loopback
        self.context = ssl.create_default_context(cafile=ca_file)
        self.provider = credential_provider
        self.scopes = tuple(credential_scopes)
        if credential_provider and (not principal or not self.scopes):
            fail('invalid-policy', 'Protected reads require an explicit principal and scopes')
        self.principal = principal or 'anonymous'
        self.max_redirects = max_redirects
        self.cache = {}; self.records = []
        self.total = 0; self.wire_total = 0; self.documents = 0

    def credentials(self, url, original_origin):
        if not self.provider or origin(url) != original_origin:
            return {}
        path = urlsplit(url).path or '/'
        if not any(origin(scope) == origin(url) and
                   (path == urlsplit(scope).path or
                    path.startswith(urlsplit(scope).path.rstrip('/') + '/'))
                   for scope in self.scopes):
            return {}
        # Only credential headers are accepted, never host/routing overrides.
        try:
            supplied = self.provider(url) or {}
            if not isinstance(supplied, dict):
                fail('invalid-policy', 'Credential provider must return headers')
            headers = {}
            for key, value in supplied.items():
                if str(key).lower() not in ('authorization', 'cookie'):
                    fail('invalid-policy', 'Credential provider returned a non-credential header')
                if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
                    fail('invalid-policy', 'Invalid credential header')
                headers[str(key).lower()] = value
            return headers
        except Failure:
            raise
        except Exception:
            fail('access-denied', 'Credential provider failed')

    def address(self, url):
        p = urlsplit(url)
        if origin(url) not in self.allowed:
            fail('access-blocked', 'Origin is not authorized')
        if not p.hostname:
            fail('access-blocked', 'Missing hostname')
        port = p.port or (443 if p.scheme == 'https' else 80)
        addresses = list(dict.fromkeys(a[4][0] for a in socket.getaddrinfo(
            p.hostname, port, type=socket.SOCK_STREAM)))
        if not addresses:
            fail('unavailable', 'Host did not resolve')
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if not (ip.is_global or (self.allow_loopback and ip.is_loopback) or
                    any(ip in n for n in self.networks)):
                fail('access-blocked', 'Network destination is not authorized')
        if p.scheme == 'http' and not (self.allow_loopback and all(
                ipaddress.ip_address(a).is_loopback for a in addresses)):
            fail('access-blocked', 'Plain HTTP requires explicit loopback development policy')
        return addresses, port

    def _body(self, handle, encoding, cap, deadline):
        if encoding not in ('identity', 'gzip'):
            fail('unsupported-encoding', 'Unsupported Content-Encoding')
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == 'gzip' else None
        result = bytearray(); wire = 0
        # Each resource is bounded on both sides of content decoding.
        while True:
            if time.monotonic() > deadline:
                fail('limit-exceeded', 'Retrieval duration exceeded')
            raw = handle.read(min(16384, cap - wire + 1))
            if not raw:
                break
            wire += len(raw); self.wire_total += len(raw)
            if wire > cap or self.wire_total > self.limits.total_bytes:
                fail('limit-exceeded', 'Transferred byte limit exceeded')
            try:
                chunk = decoder.decompress(raw, cap - len(result) + 1) if decoder else raw
            except zlib.error:
                fail('invalid-encoding', 'Invalid gzip stream')
            result.extend(chunk); self.total += len(chunk)
            if len(result) > cap or self.total > self.limits.total_bytes:
                fail('limit-exceeded', 'Decoded byte limit exceeded')
            if decoder and decoder.unused_data:
                fail('invalid-encoding', 'Trailing or concatenated gzip data')
        if decoder and not decoder.eof:
            fail('invalid-encoding', 'Truncated gzip stream')
        return bytes(result), wire

    def fetch(self, url, media=None, descriptor=False):
        original, _ = urldefrag(url)
        url = original
        cap = self.limits.descriptor_bytes if descriptor else self.limits.material_bytes
        if descriptor:
            self.documents += 1
            if self.documents > self.limits.documents:
                fail('limit-exceeded', 'Descriptor count exceeded')
        deadline = time.monotonic() + self.limits.timeout
        seen = set()
        try:
            for redirects in range(self.max_redirects + 1):
                url = resolve(url, url)  # canonical dot-segment resolution before credential scope
                candidate = urlsplit(url)
                if candidate.scheme in ('http', 'https'):
                    decoded = unquote(candidate.path)
                    if (any(ord(c) <= 32 or ord(c) == 127 for c in decoded)
                            or '\\' in decoded or '/' in unquote(candidate.path.replace('/', ''))
                            or any(part in ('.', '..') for part in decoded.split('/'))):
                        fail('access-blocked', 'Ambiguous encoded network path')
                if url in seen:
                    fail('cycle', 'Redirect loop')
                seen.add(url)
                p = urlsplit(url)
                if p.scheme == 'file':
                    if self.root is None or p.netloc or p.query:
                        fail('access-blocked', 'Local retrieval is not authorized')
                    path = Path(unquote(p.path)).resolve()
                    if not path.is_relative_to(self.root):
                        fail('access-blocked', 'Local path leaves authorized root')
                    with path.open('rb') as handle:
                        data, wire = self._body(handle, 'identity', cap, deadline)
                    return self._record(original, Response(data, url, {}), wire)
                if p.scheme not in ('http', 'https'):
                    fail('access-blocked', 'Unsupported scheme')
                address, port = self.address(url)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    fail('limit-exceeded', 'Retrieval duration exceeded')
                connection = (TLSConnection(p.hostname, port, address, remaining, self.context)
                              if p.scheme == 'https' else
                              http.client.HTTPConnection(address[0], port, timeout=remaining))
                try:
                    credentials = self.credentials(url, origin(original))
                    # Credential fingerprint separates changed authorization for
                    # a principal. Neither raw headers nor fingerprint are logged.
                    auth_digest = hashlib.sha256(repr(sorted(credentials.items())).encode()).digest()
                    key = (url, media, self.principal, auth_digest)
                    cached = self.cache.get(key)
                    headers = {'Host': p.netloc, 'Accept': media or '*/*', 'Accept-Encoding': 'gzip, identity'}
                    headers.update(credentials)
                    if cached:
                        if cached.headers.get('etag'):
                            headers['If-None-Match'] = cached.headers['etag']
                        elif cached.headers.get('last-modified'):
                            headers['If-Modified-Since'] = cached.headers['last-modified']
                    connection.request('GET', urlunsplit(('', '', p.path or '/', p.query, '')), headers=headers)
                    handle = connection.getresponse()
                    response_headers = {}
                    for name, value in handle.getheaders():
                        name = name.lower()
                        if name in ('link', 'cache-control', 'vary') and name in response_headers:
                            value = response_headers[name] + ', ' + value
                        response_headers[name] = value
                    if handle.status in (301, 302, 303, 307, 308):
                        if redirects >= self.max_redirects:
                            fail('limit-exceeded', 'Redirect limit exceeded')
                        target = response_headers.get('location')
                        if not target:
                            fail('invalid-redirect', 'Missing redirect location')
                        target = urldefrag(resolve(url, target))[0]
                        if urlsplit(target).scheme not in ('http', 'https'):
                            fail('access-blocked', 'Redirect leaves HTTP transport')
                        if p.scheme == 'https' and urlsplit(target).scheme != 'https':
                            fail('access-blocked', 'TLS downgrade redirect')
                        url = target
                        continue
                    if handle.status in (401, 403):
                        self.cache.pop(key, None)
                        fail('access-denied', 'Publication read denied')
                    if handle.status in (404, 410):
                        self.cache.pop(key, None)
                        fail('not-found', 'Resource does not exist')
                    if handle.status == 304:
                        if not cached or not any(k in headers for k in ('If-None-Match', 'If-Modified-Since')):
                            fail('invalid-cache', '304 without a conditional cache entry')
                        data = cached.data
                        merged = dict(cached.headers); merged.update(response_headers)
                        result = Response(data, url, merged, 'revalidated')
                        wire = 0
                        self.total += len(data)
                        if len(data) > cap or self.total > self.limits.total_bytes:
                            fail('limit-exceeded', 'Cached byte limit exceeded')
                    elif handle.status == 200:
                        data, wire = self._body(handle, response_headers.get('content-encoding', 'identity').lower(), cap, deadline)
                        result = Response(data, url, response_headers)
                    else:
                        fail('unavailable', 'HTTP status ' + str(handle.status))
                    actual = result.headers.get('content-type', '').split(';')[0].strip().lower()
                    if media and actual != media:
                        fail('media-mismatch', 'Content-Type differs from declaration')
                    policy = {x.strip().split('=')[0].lower() for x in result.headers.get('cache-control', '').split(',')}
                    # Unknown Vary dimensions cannot be safely keyed by this client.
                    vary = {x.strip().lower() for x in result.headers.get('vary', '').split(',') if x.strip()}
                    if 'no-store' in policy or vary - {'authorization', 'cookie', 'accept-encoding'}:
                        self.cache.pop(key, None)
                    else:
                        self.cache[key] = result
                    return self._record(original, result, wire)
                finally:
                    connection.close()
        except FileNotFoundError:
            fail('not-found', 'Local resource does not exist')
        except PermissionError:
            fail('access-denied', 'Local read denied')
        except ssl.SSLError:
            fail('tls-error', 'TLS verification or connection failed')
        except (OSError, ValueError, http.client.HTTPException):
            fail('unavailable', 'Retrieval failed')
        fail('limit-exceeded', 'Redirect limit exceeded')

    def _record(self, original, result, wire):
        # Never record response headers: they may contain Set-Cookie or challenges.
        self.records.append({'url': original, 'finalUrl': result.url,
                             'sha256': hashlib.sha256(result.data).hexdigest(),
                             'bytes': len(result.data), 'transferredBytes': wire,
                             'cache': result.cache})
        return result
