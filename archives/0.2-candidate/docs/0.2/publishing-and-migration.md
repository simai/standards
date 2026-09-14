# Publishing and migrating AI First 0.2

Status: local pilot candidate 0.2.0-rc.1. Verify its candidate lock before use.
The [core](../../spec/0.2/core.md) and
[transport contract](../../spec/0.2/discovery-and-transport.md) define the format.

## Install and read

Use Python 3.11 or later in a virtual environment:

```sh
python -m pip install -r requirements-0.2.txt
python tools/aifirst02.py validate examples/0.2/minimal
python tools/aifirst02.py list examples/0.2/minimal
python tools/aifirst02.py read examples/0.2/minimal
```

Use `--mode manifest` for a direct file/URL and `--mode page` for HTTP/HTML
page discovery. The original `tools/aifirst.py` and `requirements.txt` remain
the 0.1 reader/runtime. Choosing a handler is explicit; an unsupported wire
version is an error, never a heuristic conversion.

`validate` traverses the full inventory, checks every representation, sources,
contract locators and immediate routed manifests. Routed publications' complete
inventories must be validated separately. It never calls business operations or
claims full OpenAPI validation. `list` and `read` use indexed selectors when
available; `--full` forces whole inventory traversal. An error report can retain
successful materials but returns a nonzero exit code when completeness is partial.

## Safe local migration

```sh
python tools/aifirst02_publish.py migrate path/to/old-publication path/to/new-publication
python tools/aifirst02_publish.py migrate path/to/old-publication path/to/new-publication --apply
```

The first command performs validation and reports planned output hashes and
manual review topics. It writes nothing. The second repeats preflight, converts
all local manifests/catalogs (including routed publications), adds child revision
and byte-digest pins, validates the staged output, and writes a **new directory**.
The source is never rewritten. Existing destinations and overlapping source/output
trees are rejected. Keep the JSON report with the output for review.

Only referenced local files are copied. Unreferenced configuration, secrets and
unrelated assets are not included. Remote dependencies, old optional fields whose
names acquire 0.2 meaning, and broken publications require explicit reconciliation.
This command is a portable publication migration, not a full website backup.
Unknown optional fields retain their values unless they collide with new semantics.
No translation relationship, catalog selector, access policy or related-domain
trust is invented. The report identifies optional enrichment left to the publisher.

The destination must not be served while it is being assembled. The tool does
not atomically switch an existing website or replace a deployed publication.
An existing production build's publish/rollback mechanism remains responsible
for the final switch after validation. Keeping the old output makes rollback
straightforward and avoids disturbing concurrent product work.

## Generate AI First and llms.txt together

```sh
python tools/aifirst02_publish.py export path/to/source-publication path/to/new-export
python tools/aifirst02_publish.py export path/to/source-publication path/to/new-export --apply
```

A publisher's existing content/build pipeline produces the source 0.2 inventory
and full text representations once. This tool validates that inventory and exports
it with an llms.txt projection using the same titles, descriptions and full text
links. Code and tables remain exact representation bytes. The export includes only
referenced files; a removed item therefore does not survive through a directory
copy. Existing llms.txt files require reconciliation, rather than silent replacement.

Each published item needs a full Markdown or plain-text representation for joint
text export. Add that representation through the existing content renderer;
this tool does not reverse-engineer arbitrary HTML or invent component semantics.
See the [generated example](../../examples/0.2/joint-export/llms.txt).

## Protected reads and corporate deployments

Credentials are only supplied through the Python API, never command-line tokens
or publication files. A caller provides `credential_provider`, `principal` and
`credential_scopes` to `Reader`. The provider returns Authorization/Cookie headers
for an allowed scope. Separate client objects and principal labels isolate users;
credential changes also isolate cached entries. No OAuth flow is implemented.

Use caller-controlled `allow_origins`, `allow_networks` and `ca_file` for approved
corporate addresses and trust anchors. Both origin and network authorization are
required. HTTP is restricted to explicitly enabled loopback development. HTTPS
verification remains mandatory even for corporate/private networks. Related-resource
links do not configure these policies. Browser deployment requirements are in the
transport contract; CORS and site authentication remain publisher responsibilities.

## JavaScript baseline reader

```sh
node tools/aifirst02.mjs list examples/0.2/minimal
node tools/aifirst02.mjs read examples/0.2/minimal
node tools/aifirst02.mjs read https://example.org/docs/ --language en
```

Node 20 or later is required. The implementation reads the bundled 0.2 schemas
and has no Python or npm runtime dependency. It handles knowledge publications,
JSON validation, basic HTTP/HTML discovery, scoped routes, pinned/selective
catalogs, exact selection and full text/digest/provenance. It validates every
resolved address before pinning a request and retains HTTPS verification.

This is a second reference implementation from the same project, not an
independent external adoption. It is intentionally a baseline: identity encoding,
no credential provider/cache, no corporate network allowlist, no capability
contract binding and no language fallback. Unsupported required profiles fail
explicitly. Its IP policy is conservative and may reject special-purpose ranges
which a more capable configured client can use. Python provides the broader 0.2
reference profile. Browser deployment uses normal browser security and is
specified separately; this Node client is not a browser extension or OAuth client.

The common corpus is in `conformance/0.2/shared-cases.json`. Set `AI_FIRST_NODE`
to a working Node executable when running Python's complete test suite if the
default `node` command is unavailable. Missing Node is an explicit skipped check,
never evidence of cross-reader compatibility.

## Reproduce the benchmark

```sh
python tools/benchmark02.py
```

The benchmark generates 100,000 synthetic records in a temporary local site and
retrieves one selected shard using default reader limits. It also compares HTML,
llms.txt and AI First on four fixed exact-version/language tasks with identical
materials. It measures selection, preserved bytes, requests and transfer volume.
The script reports deterministic parser behavior, not model intelligence or user
productivity. Human publishing time and peak memory are not measured.
