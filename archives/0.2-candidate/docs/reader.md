# Reader and validator guide

The reference CLI requires Python 3.11+ and the pinned jsonschema dependency.
Run it from the checkout; it locates its bundled schemas relative to its file.
There is no globally installed command or network-fetched schema requirement.

| Command | Outcome |
| --- | --- |
| validate DIR | Check the manifest, catalogs, representations, sources and known contracts |
| validate FILE --mode manifest --structure-only | Check just one manifest or catalog |
| list DIR | Return all published items and partial-inventory errors |
| read DIR --id ID | Return one full supported representation and provenance |
| read URL --mode page | Discover through marked HTML link or origin-root route |

Filters `--query`, `--product`, `--version`, `--language` and `--id` combine with
AND. Query is a case-insensitive token substring filter over title and description,
not a semantic search engine. `read` refuses multiple matches and partial catalogs.
`list` preserves partial findings and exits nonzero when traversal failed.

Outputs are JSON. Exit 0 means the requested check/read completed without errors;
exit 1 means a documented operational or conformance failure; argparse usage errors
exit 2. `runtimeConformance` remains not-run. Read output's text is a JSON string
whose decoded UTF-8 bytes equal the selected material; it is not executed.

The reference reader supports full UTF-8 text/markdown, text/plain, text/html and
application/json. It retrieves whole documents, not HTML fragments or rendered
pages. Publication validation can check bytes/digests for other declared MIME types.
Reading an unsupported media type reports unsupported-media.

Network policy defaults to the entry origin only. Add a specific trusted origin
with `--allow-origin https://docs.example.org` if your task permits it. This does
not permit private network destinations or credential forwarding. Local files
remain within the supplied root; remote content cannot read local files. The
reference transport pins a validated public IP while verifying TLS for the
original hostname. Redirects are deliberately rejected. Loopback HTTP requires
`--allow-loopback`. It never calls advertised endpoints or sends POST requests.

A Python integrator can import Reader and Limits from tools/aifirst.py. Create a
new Reader for each operation: budgets and retrieval evidence are operation-local.
Call discover(mode), inventory(), then select()/material() or publication(). The
library raises Failure with a machine-readable code. Applications should render
results as untrusted data and retain provenance outside model-generated prose.

## Limits and unsupported behavior
Default limits are those in D03. The library permits stricter Limits. CLI defaults
are fixed in 0.1. No persistent cache, cookies, OAuth session, custom DNS/proxy
configuration, operation executor, ZIP unpacking, signature verifier, PDF text
extractor or automatic language fallback is included. These omissions are explicit
boundaries, not evidence that such features would be safe to infer.

See conformance/acceptance.md for the actual tested environment. The implementation
is one reference, not independent adoption or certification of other readers.

For root inputs, the declared scope must cover the supplied root as well as any
selected child route. The publication report's structure dimension includes
retrieved catalogs; an unavailable catalog is a publication failure, while a
retrieved malformed catalog also fails structure.
