# Initial implementation acceptance

Date: 2026-09-09. Distribution: 0.1.0. Wire format: 0.1.
Status: **PASS WITH NOTES for local pilot adoption**. All 49 tests passed.
Repository link/language checks and five publication validations passed.

## Accepted outcome and corpus
The requested outcome is a complete bounded specification that projects can begin
using. The accepted architecture is a small ai.json entry, optional catalogs,
ordinary material representations and references to existing operation contracts.
The finite corpus is minimal/local knowledge, versioned catalogs, a static shared
site, a capability descriptor and their declared error and access boundaries.
It does not include production installation or executing business actions.

## Evidence dimensions
| Dimension | Evidence and limit |
| --- | --- |
| Structure | Draft 2020-12 schemas, strict JSON and compatibility fixtures |
| Publication | Local and ephemeral HTTP end-to-end tests; examples and repository self-description |
| Reader behavior | Exact bytes, applicability filters, provenance and explicit partial/ambiguous outcomes |
| Safety boundaries | Escapes, symlinks, blocked origins/IPs, pinned TLS transport unit test and no action execution |
| Runtime operations | Not run; no executor or production credentials |
| Independent adoption | Not run; all included implementations and examples are first-party |
| Hosted CI | Workflow provided; remote runs have not been triggered or observed |

Actual public HTTPS endpoint interoperability is not claimed. HTTP transport is
tested on loopback; TLS destination pinning and hostname use are unit-tested. The
configured Python CI matrix is 3.11/3.14; the local run records its actual runtime.

## Manual specification review
- One small manifest is sufficient; an external catalog, graph engine and server
  runtime are not mandatory.
- Required/optional fields, absence, unknown requirements, errors, scope and
  publication revisions have explicit semantics.
- Knowledge sources and capability contracts remain authoritative. Metadata
  cannot grant authorization or validate truth by assertion.
- Examples expose fictional public data only. There are no credentials or
  production targets; example.invalid is deliberately non-operational.
- No simulated independent implementation or fabricated international acceptance
  is used to promote the release.
- AI First development metadata in graph/ and .simai/ is outside the wire format
  and root public-material allowlist.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_repository.py
python3 tools/build_manifest.py --check
```

Use the virtual environment described in docs/quickstart.md. Machine-readable
results are in verification.json after final verification. Its file hashes bind
implementation/specification inputs, not the report itself.

## Final measured result

49 tests passed in 1.115 seconds on macOS arm64, Python 3.14.4, jsonschema 4.26.0.
The suite includes ten real loopback HTTP tests. The root publication exposes ten
public documents; all four example publications validate. Rebuilding the root
manifest is deterministic, and source changes update item and snapshot revisions.
No branch, commit, push, public release or production deployment was performed.

The bounded local delivery is complete. External adoption, live capability runtime
checks and institutional standardization remain explicitly outside its acceptance.

## Separate repository-process limitation
The SIMAI repository-process final checker did not pass. It expects its own typed
workflow/source/step/check evidence and a configured Project Technology inventory;
the product's conformance report is not that evidence format. The project bootstrap
also has no accepted target binding. Repeating with the original task wording did
not resolve this. No control-plane PASS or federation-governed completion is claimed.
This is distinct from the 49 passing product tests and local pilot-usage evidence.
No federation policy, canonical graph or checker was modified to bypass the result.
