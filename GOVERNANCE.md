# Governance and support

The repository owner is the initial editor and release authority. No independent
standards body or multi-organization consensus is represented. Contributions do
not require SIMAI tooling. Propose changes with scenarios, compatibility effects,
normative prose, schemas, examples and reproducible tests through issues or pull requests.

## Stable maintainer release

On 2026-09-14 the owner requested a usable release of both standards at version
1.0 or later and authorized autonomous release preparation. This release adopts
**maintainer-supported stable specification** as a separate maturity category.
Its acceptance requires complete bounded specifications, executable tooling,
regression and failure-case checks, immutable historical inputs, migration guidance,
a digest inventory and an identifiable release revision.

Product pilot acceptance and independent ecosystem adoption are separate evidence
tracks. Their absence is disclosed and does not prevent this maintainer release.
The earlier product-backed gate remains available as `tools/check_stable10.py`;
it is not the acceptance gate for this distribution and must not report fictitious
pilot success. Stable community specification and formal international recognition
still require their own external evidence and process.

## Compatibility commitment

The distribution, specification edition, wire format and subject standard version
are separate identities. AI First 1.0.0 uses wire `1.0`. Standard Contract 1.0.0
uses envelope `1.0` and optional lifecycle record version `1.0`.

PATCH preserves normative meaning. MINOR adds compatible optional functionality.
Incompatible obligations or parser semantics require MAJOR and an explicit
migration. Never overwrite a published version or silently upgrade a project's
pinned dependencies. Historical formats retain their original handlers and bytes.

Report defects with a minimal reproduction. Maintainers triage issues, publish
fixes as new releases and document deprecation/withdrawal. No response-time SLA,
independent audit or warranty is implied. Existing license terms apply.
