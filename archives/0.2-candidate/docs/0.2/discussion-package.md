# AI First 0.2 discussion package

Status: preparation draft. No public release or outreach has been performed.
Product pilots are pending; this document must not be presented as pilot-backed
international readiness until their actual results have been accepted.

## Problem and audience

A client often needs the correct product version and language of a document,
its complete code example, and an attributable source. A whole website download
is an expensive substitute for a small publication index. AI First proposes a
small JSON envelope plus ordinary readable files, with optional catalogs and
existing API-contract locators. Publishers include static sites, documentation
generators, CMSs, application platforms and internal knowledge services.

The [0.2 core](../../spec/0.2/core.md) specifies identities, revisions, selectors,
translations and access hints. The [transport contract](../../spec/0.2/discovery-and-transport.md)
specifies discovery and bounded reads. The
[publisher/migration guide](publishing-and-migration.md) covers runnable tools.
The [manifest schema](../../schemas/0.2/manifest.schema.json) and
[catalog schema](../../schemas/0.2/catalog.schema.json) are machine-readable.

## Relation to existing work

| Existing initiative | Reuse or boundary |
| --- | --- |
| [llms.txt v2](https://llmstxt.org/) | Human/agent-readable curated Markdown index, with subpath and Link discovery. Generate it alongside AI First; structured revision pins and exact applicability are AI First's additional contract. |
| [OpenAPI](https://spec.openapis.org/oas/v3.2.0.html) | Existing HTTP operation descriptions remain authoritative. AI First points to their operations and does not duplicate input/output schemas or execute them. |
| [MCP authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) | Existing authorization mechanisms belong to the applicable protocol/provider. AI First does not replace OAuth or grant business permissions. |
| [A2A discovery](https://a2a-protocol.org/latest/topics/agent-discovery/) | Agent discovery and interaction are separate from discovering readable publication material. An AI First resource is not automatically an A2A agent. |

These distinctions are design choices, not evidence that a separate new format
will be adopted. Existing ai.json files may have another meaning; recognize the
format marker and use a direct address or marked link rather than overwriting a
collision. No exclusive filename ownership, registration or institutional status
is claimed.

## Current evidence and limitations

The [synthetic benchmark](../../conformance/0.2/benchmark.json) demonstrates a
100,000-item publication with 500 catalogs. Selection retrieves one catalog and
one material after the manifest: three HTTP requests and 157,553 body bytes in
the recorded run. Reader limits were not raised. This is a selective network
retrieval result, not a measurement of peak memory or real-world latency.

Four fixed version/language tasks compare ordinary HTML, llms.txt and AI First
using the same metadata and exact material bytes. All three succeeded. In the
small fixture, AI First transfers more metadata. No claim is made that it reduces
tokens on every site, improves a model's reasoning, or saves a measured number
of developer hours. A real publication pipeline and human/model task study are
needed to assess those outcomes.

The [shared corpus](../../conformance/0.2/shared-cases.json) checks Python and
JavaScript baseline selection and failure behavior. Local HTTPS tests verify
trusted certificates, hostname validation and actual discovery/read behavior.
The JavaScript tool is another reference implementation from this project; it
is not independent external adoption. Its supported subset is documented.

Docara and Larena, when implemented, are two product integrations from one
ecosystem. Their current existence is not evidence that these pilots ran.
Only returned code revisions, reproducible builds and scenario evidence can
change their status to implemented or compatible.

## Questions for external implementers

1. Is the minimum manifest small enough for a manually maintained site?
2. Are conservative exhaustive catalog bounds practical to generate, or does
   your catalog need another optional index profile?
3. Does the format preserve the language/version meaning in your publishing
   system without forcing a new content model?
4. Which existing access systems make documentation-readable authorization
   difficult, and what descriptive hints would help without embedding secrets?
5. Does joint llms.txt generation fit your current workflow? Which information
   should remain editorial instead of generated?
6. Are the unregistered discovery marker and filename collision rules clear?
7. Can a developer outside this ecosystem implement the baseline from the prose
   and fixtures without consulting the Python source?
8. Which unsupported cases justify an extension rather than a larger mandatory core?

## Readiness rules

Readiness for handoff requires a frozen, hashed candidate, reproducible tools,
passing applicable tests, honest evidence and both product handoff files.
Pilot-backed discussion readiness additionally requires both returned pilots,
compatibility acceptance and an updated evidence package. Community outreach,
release, production deployment and international recognition remain separate
future actions. This repository cannot self-award international recognition.
