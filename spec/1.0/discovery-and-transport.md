# AI First 1.0 discovery and transport

## Entry selection

An explicit manifest address supplied by the caller has priority and bypasses
page discovery. A caller-supplied resource root discovers `ai.json` relative to
that directory, including subdirectory roots. Do not overwrite an existing
unrecognized ai.json. Extensionless explicit addresses are supported when their
response media type is `application/json`.

For page discovery, retrieve the page and collect declarations from both HTTP
`Link` headers and HTML `link` elements. A declaration is recognized only when
`rel` includes `describedby`, its `type` is `application/json`, and it explicitly
identifies AI First 1.0: HTTP parameter `ai-first="1.0"`, or HTML attribute
`data-ai-first="1.0"`. Other describedby links are unrelated metadata.

```html
<link rel="describedby" type="application/json" data-ai-first="1.0" href="./ai.json">
```

```http
Link: <./ai.json>; rel="describedby"; type="application/json"; ai-first="1.0"
```

Resolve each link relative to the final page URL. Ignore HTML base elements for
this protocol. Identical normalized targets collapse; distinct recognized
targets produce `ambiguous-discovery`, including header/HTML disagreement.
The fallback when there is no declaration is origin-root `/ai.json`. A client
wanting subpath discovery without a declaration supplies that resource root.
A fetched declaration that fails is an error, not a reason to silently fall back.
No well-known URL, MIME registration or link-parameter registration is claimed.

Validate declared resource scope against the page and follow the longest
matching subordinate route, with depth and cycle limits. Related external
resources are explicit navigation, not automatic routing.

## Retrieval

Readers MUST validate each original and redirected destination against caller
origin, network and local-root policy. HTTPS certificate and hostname validation
are mandatory. DNS results MUST be checked and connections pinned to a checked
address while retaining TLS hostname verification. Private destinations require
explicit caller-configured networks in addition to origin authorization; a
manifest cannot add either. Local files MUST stay inside the resolved local root,
including symlink resolution. Online publications cannot authorize local reads.

Only GET retrieval is part of this standard. Follow at most five redirects by
default (301, 302, 303, 307, 308). Reject loops, missing Location, HTTPS-to-HTTP
downgrades and unauthorized destinations. Do not forward credentials across an
origin change. Resolve content-relative links against the final retrieval URL.
Record original and final addresses so redirect provenance is visible.

Support identity and gzip content encoding. Bound compressed bytes, decompressed
bytes, total transfer/decoded volume, descriptors, item count, depth, redirects
and request duration. Hash decompressed representation bytes. Truncated gzip,
invalid CRC/trailing data and over-expansion are errors. Unsupported encoding
fails explicitly. Content-Type must match the declared representation type
(disregarding parameters); decoding does not change MIME identity.

## Caching

A reference client MAY maintain an in-memory, principal-isolated cache and
revalidate with ETag/If-None-Match or Last-Modified/If-Modified-Since. A 304 without
a matching cache entry is an error. Validate cached bytes against the current
link pin and size policy. Respect no-store; no-cache requires revalidation.
This specification does not require stale-on-error serving. Report whether bytes came
from a 200 response or validated cache. A 304 is transport freshness evidence,
not proof that all publication shards are mutually consistent. Do not share
protected caches between identities, even when URLs and validators are equal.

## Browser publishers

Same-origin reads work under normal browser rules. For cross-origin clients,
configure CORS on manifests, catalogs and materials, allow GET, and expose Link,
ETag and Last-Modified as needed. Credentialed CORS requires explicit allowed
origins and a compatible existing authentication design. Do not publish a
wildcard credential policy. Browser JavaScript cannot independently pin DNS or
read hidden response headers; report this implementation boundary. CORS is not
an authorization mechanism and does not grant access to business operations.

