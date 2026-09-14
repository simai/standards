# AI First 0.2 candidate acceptance map

This is a requirement-level map for local handoff readiness. It is not an
international certification, independent adoption claim or completed product pilot.
The executable checks and their limitations take precedence over broad labels.

| Approved requirement | Implemented evidence | Boundary or remaining external evidence |
| --- | --- | --- |
| Preserve 0.1 | `conformance/0.1-baseline.json`; original reader/schemas/examples; 49 unchanged tests | Only legacy CI command narrowed to its original suite; original file saved locally. |
| Small core; optional features | Separate 0.2 schemas; core and profile requirements in spec | Capability/access features need their applicable reader. |
| Small site, docs, local copies, subpaths | Minimal/service/joint examples; reader and routing tests | Product-generated examples arrive through pilots. |
| Large catalogs | Reproducible 100k HTTP benchmark; default limits; one selected shard | Peak memory not measured; no server search. |
| Explicit and HTTP/HTML discovery | Reader discovery tests plus Python/JS HTTPS integration | Node baseline HTML parsing is limited to metadata discovery; browser integration is documented, not a browser pilot. |
| Independent revisions, digests, partial results | Core tests: pins, repeated links, cycles, selectors, unrelated missing material | Targeted absence depends on publisher index assertions. |
| Redirects, gzip, cache, TLS | Transport tests: limits, corrupt gzip, revalidation, no-store, trust/hostname failures | JavaScript baseline identity-only; full transport features are in Python. |
| Exact versions and translations | Exact selection and explicit fallback with translation identity | Translation quality/equivalence is publisher-owned. |
| OpenAPI 3.0–3.2 JSON/YAML | Contract tests: all versions/media, references, unsafe YAML, 3.2 methods | Locator checks only; no full API validation or execution. |
| Protected reading and private addresses | Python provider scopes, actor cache separation, redirect credential isolation, explicit networks | Actual Larena Access/tenant behavior awaits its executor. |
| Related domains without trust expansion | Related links are descriptive, not traversed; external reads need caller origin policy | No federation or automatic domain discovery. |
| Safe migration | Dry-run, pinned catalogs, new output, broken-input/collision and preservation tests | Offline referenced dependencies only; server configuration needs review. |
| Joint generation | One metadata/material inventory produces both exports; exact bytes retained | Existing product build/IR adapters belong to product executors. |
| Second language implementation | Standalone Node reader, 12-case corpus, actual HTTPS comparison | Same project authorship; baseline subset, not independent adoption. |
| Fair comparison | Four deterministic tasks; all formats succeed; actual requests/bytes in benchmark | No model/user accuracy or measured developer-hour claims. |
| Versioned product handoffs | Two standalone handoff files plus candidate lock and return schema/inspector | User transfers links; no product task creation or chat messages. |
| Pilot acceptance | Return inspector validates hashes and local publication compatibility | Both actual pilots and scenario review are pending. |
| English discussion package | Problem, audience, primary-source comparison, evidence, limitations and questions | Add actual pilot outcomes before pilot-backed discussion readiness. |
| Process versus product evidence | Separate workflow/process receipts; original 0.1 report preserved | Federation process-selection/context gap is explicit; never replaced by product test PASS. |

## Evidence interpretation

A passing test suite is local implementation evidence. A verified candidate lock
is integrity evidence. A passing returned-publication check is compatibility for
those exact returned bytes. None alone proves product build lifecycle, protected
HTTP access, independent adoption or international recognition.

Before accepting a pilot, inspect all required scenario evidence and reproduce
applicable commands under the product owner's authorized scope. Standard defects
are fixed here with a new candidate revision; integration defects are returned to
the existing product owner. Keep candidate readiness, handoff readiness, user
transfer, pilot implementation and compatibility acceptance as separate states.
