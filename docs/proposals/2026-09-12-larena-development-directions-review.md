# Review and proposed roadmap: Larena development directions

Date: 2026-09-12.
Status: proposal for discussion; no accepted wire change, new profile, version,
package, implementation assignment or pilot acceptance is created by this review.
The requested deliverable is analysis and a justified plan. The existing frozen
candidate and product handoffs remain unchanged.

## Recommendation

Keep the mandatory core unchanged. First demonstrate the requested outcomes using
existing publication items and authoritative external contracts. Introduce at most
one narrowly scoped optional semantic extension at a time, only after a fixture
proves that ordinary materials and existing links cannot give a compatible client
a deterministic answer. Do not promise four new profiles from four product needs.

Ideal result: an unfamiliar compatible client finds the relevant context and real
contract, distinguishes publisher assertions from observations, explains missing
information and respects visibility, without per-project prompts or a mandatory
service graph, workflow engine or evidence ledger.

The architectural tension is richer automated reasoning versus a small manual-site
format. Separate optional semantic documents from the required resource envelope;
reuse domain-owned schemas and execution systems. This avoids putting the cost of
a distributed application's model on every small site.

## Sources and verified baseline

The incoming source is the Larena specs handoff named
`docs/project-management/handoffs/2026-09-12-ai-first-development-directions.md`
in the `larena-specs` repository. Its SHA-256 is
`9ec84adbc86b6cb8a98c9055ffdfbea3b2e1770c0f90b2b6a46f637d88d801b9`.
It explicitly declares itself a product request, not a pilot result or accepted
format amendment.

The accompanying `larena-specs/specs/standards/larena-ai-first-contract-v1.json`
has SHA-256 `ea17cc0af92854f863e3148a88401924804e630652a8ebc1a143dd1cbf105e4b`.
Its status is `proposed`; it explicitly does not authorize implementation or
change Minimal CMS membership/dependencies. Package specifications for core,
access, rest, setting, mcp, workflow, automation and ai-provider describe owner
boundaries; their planning status is not proof those features exist at runtime.
No product implementation checkout or production system was inspected here.

Current AI First evidence:

- [Candidate inventory](../../conformance/0.2/candidate.json): `0.2.0-rc.1`, wire
  `0.2`; all 101 pinned files verified unchanged on this review date.
- [Verification record](../../conformance/0.2/verification.json): historical local
  suite of 99 passing tests; not rerun or represented as a new runtime result.
- [Pilot status](../../conformance/0.2/pilots/status.json): neither returned receipt
  is recorded; both implementation/compatibility flags remain false. The new
  directions handoff does not change that state.
- [Inherited core](../../spec/core.md), [0.2 core](../../spec/0.2/core.md),
  [security](../../spec/security.md), [transport](../../spec/0.2/discovery-and-transport.md),
  [capability profile](../../profiles/capability.md) and
  [current publishing guide](../0.2/publishing-and-migration.md) are the contract.
- [Python reader](../../tools/aifirst02.py), [catalog traversal](../../tools/aifirst02_core.py),
  [transport](../../tools/aifirst02_transport.py) and
  [return inspector](../../tools/check_pilot02.py) establish implementation limits.

The repository HEAD is `37e9f29eab422866e58838f7cd32b125b650d492`; the candidate is
identified by its lock, not HEAD alone, because its files are untracked locally.
The lock SHA-256 is `7ac995ceae305c20189e668d552e98502a0c5fe04bbbbee47bb80c1c686f6ef2`.

## Need-to-coverage matrix

| Need | Classification | Existing support and exact gap | Recommended location |
| --- | --- | --- | --- |
| Understand an unfamiliar resource | Already covered | Resource identity, purpose, scope and items; requires a compatible client, not automatic support in all LLMs. | Core, unchanged |
| Read exact documentation version/language | Already covered | Exact appliesTo, translations, full representations, revision/digest checks. | Existing profiles |
| Distinguish product from address | Covered plus clarification | IDs are not locations; product applicability is separate from publication revision. No formal installation model exists. | Examples first |
| Identify installed services and dependencies | Optional semantic candidate | related has free-text relation but no controlled predicates, typed subject/object or installed-state proof. | Optional linked topology description |
| Represent monolith and remote placement | Covered navigation; missing semantic mapping | routes are URL subscopes; related permits separate resources. Neither proves runtime containment or wiring. | Topology examples/client policy |
| Find an outcome-oriented scenario | Covered as knowledge; clarification | A knowledge item can contain prerequisites/results and links. No standard structured scenario interpretation exists. | Structured material convention first |
| Detect a missing prerequisite deterministically | Candidate semantic gap | Text alone is not a machine-readable capability dependency contract. Omission may also mean inaccessible or incomplete. | Domain scenario schema; optional binding if reusable |
| Choose a compatible provider | Candidate semantic gap | An operation pointer and exact version do not compare formats, modes or limits. | Domain-owned requirement/provider schemas and evaluator |
| Distinguish assertion from observation | Partial support; clarification first | Source/digest/cache provenance exist; no general observation, checker or validity interval model. | Evidence material; optional reference envelope later |
| Prove current service health | Outside core | HTTP cache revalidation validates a retrieved representation, not the business service. | Product monitoring/checker |
| Hide names and topology from unauthorized actors | Existing invariant; stronger examples/tests needed | Publisher filtering and principal caches exist; a link to denied content can itself disclose a sensitive name. | Publisher projections and client redaction |
| Human/AI representations from one source | Covered approach, product integration pending | Joint export reuses one publication inventory; product Document IR/registry integration is not completed. | Integrator |
| Per-button or DOM manifest | Not justified | Items identify knowledge/capabilities; UI-element semantics are not established. | Keep outside core; link authoritative UI/tool contract if needed |
| Execute or switch a service | Outside standard | Description is not authorization, orchestration, secret storage or a configuration apply operation. | Product Access/runtime/workflow |

## Findings that constrain the design

1. A free-text `related.relation` can carry a human explanation today, but giving
   values such as "installed" universal machine semantics is a contract change.
   Unknown optional fields being allowed by a schema does not make them portable.
2. `complete` currently describes the visited publication catalog closure. Related
   resources are not traversed. A locally complete publication can coexist with an
   unavailable related service. A future client must report publication completeness
   and multi-resource discovery/assessment coverage separately, not redefine 0.2.
3. `appliesTo` identifies exact product versions; it is not a service compatibility
   verdict, installation ID or version-range language. Separate these identities
   in examples before designing new fields.
4. `freshness: revalidated` in reader output is an HTTP cache observation. It does
   not establish current capability availability, actor permission or tenant
   compatibility. Documentation should make the object of freshness explicit.
5. The current CLI returns selected items and retrieval records, not a topology
   view of `related`. Discovering richer composition will need an explicit client
   interface as well as a publication convention; accepting a field in a schema
   is insufficient evidence of client support.
6. Raw catalog error/provenance records can contain URLs and item IDs. This is
   acceptable only for an authorized audience. Before exposing reader output to
   a model or another user, the integration must filter sensitive metadata and
   error context, not merely deny the final material request. No new leak is
   claimed reproduced here; this is a source-backed boundary requiring tests.
7. The proposed Larena contract lists actor, execution, compensation, receipt and
   policy concerns owned by its packages. Copying that entire descriptor into
   AI First's required item fields would create a second domain model and make
   small-site adoption unnecessarily expensive.

## Decisions proposed for the four directions

### A. System composition: experiment first; optional typed links only if needed

Retain resource/product identities and ordinary locations. In a demonstration,
use distinct opaque installation identifiers and point to an authoritative
composition document published for the authorized actor. Do not infer installation
identity from a hostname or publisher name. Present mono/remote placements of the
same capability without claiming that URL nesting represents runtime ownership.

Evaluate a small set of typed relationships only where each changes a testable
client answer: uses, provides and requires. Keep product-version applicability
in its existing field. An installation relationship is initially a publisher
assertion; observation evidence can corroborate a specific binding/revision later.
Do not add a mandatory infrastructure database, registry, global graph traversal
or distributed consistency protocol.

Promotion condition: the same bounded relation model solves two deployment shapes
and a second, non-Larena fixture without package-specific field interpretation.
If a linked composition document plus a domain adapter is sufficient, do not
standardize a new AI First profile.

### B. Outcome scenarios: recommend a documentation convention now

Publish one scenario as a knowledge item with goal, input, prerequisites, required
capability references, expected result, restrictions, approval boundaries and
verification instructions. Human and AI views derive from the same source.
Use a domain-owned JSON representation alongside the readable one only when its
semantics can be kept equivalent. The reference reader retrieves it; a generic
reader does not thereby become a workflow interpreter.

Demonstrate an assortment-import scenario where a required validation capability
is missing. Expected answer: missing/unknown prerequisite and no executable plan
claim; no fabricated API. A hidden prerequisite must not be reported as globally
absent. Distinguish unavailable, unauthorized-to-disclose and genuinely absent
within a complete authorized inventory.

Defer a formal scenario profile until independent clients need to interpret the
same prerequisite/result semantics. Reject checkpoints, retries, compensation,
scheduling and execution state in the mandatory core; those remain with the
project's process engine.

### C. Compatibility: domain evaluation before a generic profile

Separate consumer requirements, supplier declarations and the comparison result.
Start with an image-processing domain fixture. A requires synchronous PNG-to-WebP
processing with alpha preservation and input size 12 MiB. Provider X declares
JPEG-only synchronous processing; Provider Y declares PNG/WebP and alpha but has
no verified size-limit observation. Expected result: X is incompatible for the
format requirement; Y is not yet proven compatible. Adding valid size evidence
can make Y compatible for those exact requirements, not for every use case.

The comparison engine is deterministic and domain-owned. The model explains its
result. Consider only a common reference envelope identifying the requirement
schema, requirement instance, provider contract, exact revisions/digests and
assessment evidence. Do not create a universal compatibility language, infer a
match from names, or extend product-version matching to ranges by accident.

A configuration-change proposal can cite the assessment; actually switching the
service remains a separately authorized product operation with its own safeguards.

### D. Provenance, freshness and trust: clarify now, evidence envelope later

First document the distinction among publisher statement, bytes fetched, contract
locator checked and business behavior observed. No digest is a signature, and no
signature would establish correctness or availability on its own.

Use a domain evidence document bound to a subject, contract/configuration revision,
check method/version, observation time, actor/tenant or public scope, result and
validity conditions. The consumer supplies trust policy and its current clock.
Evidence for the wrong revision/scope, expired evidence, a clock anomaly or an
untrusted checker yields unknown/unusable evidence, not a silently refreshed pass.
Time-to-live is not the only invalidation condition: a configuration or permission
change can invalidate an observation before expiry.

Only standardize a minimal evidence-reference convention if both composition and
compatibility demonstrations need the same semantics. Defer signatures, trust-store
exchange and key discovery until a concrete signing/revocation need is demonstrated.
Do not introduce mandatory live health checks; checks with side effects stay outside
the publication reader.

## Proposed stages, owners and acceptance

This sequence is a plan for later approval, not authorization to implement it.
Product pilot execution can proceed in its existing owner tasks; isolated standard
experiments need not wait, but cannot be labelled product evidence.

| Stage | Owner and dependencies | Deliverable and acceptance | Stop/decision boundary |
| --- | --- | --- | --- |
| 1. Establish baseline and terminology | AI First owner; current review | This matrix; unchanged lock; explicit absent pilot receipts; distinguish resource/product/installation/location and publication/assessment coverage. | No accepted profile IDs or new fields. |
| 2. Complete existing minimum pilot | Existing Larena executor; original handoff and current product contracts | Documentation plus setting.site.read, real HTTP locator or honest internal binding, actor/tenant visibility evidence; exact code/build receipt accepted here. Docara retains its own pilot. | No new business endpoint, packages or product-scope changes for the standard. |
| 3. Two-resource composition demo | AI First owner; isolated synthetic data, proposed experiment approval | Same capability in monolithic and remote layouts; explicit external navigation, denied metadata, unavailable related service, wrong installation assertion. Small-site baseline still unchanged. | If ordinary materials suffice, retain them; if typed semantics are necessary, document exact gap before schema design. |
| 4. Scenario and compatibility demo | AI First owner plus domain contract owner; stage 3 identity definitions | One import scenario and one image-provider comparison, including missing/hidden prerequisite and compatible/incompatible/unknown outcomes. Equivalent human and machine examples. | No runtime execution, infrastructure switching or universal rule language. |
| 5. Evidence-bound negative corpus | AI First owner/client implementer; stage 4 assessment | Expired, wrong revision/tenant, untrusted and unavailable evidence; deterministic decisions; URLs/names absent from unauthorized output/cache. Injected instructions do not alter client policy. | Metadata leakage blocks promotion. Signing remains deferred. |
| 6. Minimal extension decision | Standard owner with implementer review; measured gaps from stages 3–5 | For each retained extension: purpose, domain owner, schema, positive fixture, negative corpus, unsupported-reader behavior and migration impact. Prefer zero new core fields. | Explicit acceptance before modifying a normative contract. No automatic commitment to 0.3 or a profile name. |
| 7. New candidate and interoperability validation | Standard owner after stage 6 acceptance | New immutable candidate/lock, old-reader regressions, at least two client implementations for standardized semantics, updated user-transfer handoffs. | Old candidates remain unchanged; partial-reader support reported accurately; no public release implied. |

Stage 1 is completed by this analysis. All later stages are proposed/pending,
except existing product work which retains its original independent authorization.
The new incoming document is not proof of stage 2 completion.

## Work split and acceptance budget

- Documentation: terminology, separate evidence dimensions, visibility examples,
  domain recipes and explicit limits. Place proposals outside the frozen 0.2 files.
- Wire contract: only proven machine semantics needing interoperable interpretation.
  New required semantics declare their requirement explicitly; unsupported readers
  fail instead of interpreting approximate meanings. An optional readable companion
  publication may remain usable when a separate advanced publication is unsupported.
- Client: bounded explicit navigation, selective context projection, deterministic
  domain assessment hooks, evidence expiry/scope policy and precise unknown results.
  LLM reasoning never substitutes for digest, network, cache or permission checks.
- Integrator: actor-filtered generation from package/IR sources, stable identities,
  real contract links and authoritative visibility. No manual duplicate policies.

For every experiment record manifest required-field delta (target: zero), number
of publisher-maintained facts, generated versus manual data, client-specific code,
request/byte counts and selection outcomes on the fixed fixtures. Capture actual
maintenance time only if measured. A profile is justified by removed bespoke client
interpretation and repeatable outcomes, not by the size of a JSON document.

## Minimal Larena changes to assess with its owner

For the existing pilot, identify a bounded exporter/projection in the current
architecture; map package-owned operations to documentation/contract references;
apply Access to names, descriptors, links and materials; generate stable source,
revision and exact version data; supply reproducible public/synthetic fixtures.
The product executor determines whether these are changes or existing capabilities.
Nothing in the specs-only intake proves a new package is necessary.

For the proposed experiments, only contribute a sanitized installed-composition
fixture, one authoritative scenario description and the relevant domain requirement
schema/check result if those already exist or are separately approved. Reuse
existing registry, REST/OpenAPI and Access contracts. Workflow/automation retain
execution semantics; MCP retains its actual negotiation/transport; ai-provider
and a local LLM are not prerequisites for exposing publication material.

Do not change Minimal CMS membership, shared operation ownership, package dependency
graphs, secret handling, service switching, authorization, OAuth or transaction
semantics through an AI First adoption task. UI controls need no individual
manifest. Any new product surface returns to the product owner as a separate
proposal, not an instruction hidden in this standard plan.

## Decision and continuation

Recommended now: accept the direction of scenario-driven experiments with an
unchanged core, not a bundle of new profiles. Prioritize visibility and evidence
scope as cross-cutting constraints, then composition, one scenario and one domain
comparison. Defer generic compatibility, signatures and formal executable scenarios.
Reject automatic discovery-as-permission, topology-as-installed-proof and schema-
valid-as-runtime-compatible shortcuts.

No normative or product file was changed for this review. No message was sent,
pilot marked complete or old blocked delivery goal silently resumed. Formal
federation process acceptance is separate from this analysis: the initial route
misclassified the source product as the delivery owner; the corrected route chose
teamlead. The central fallback was used because no local route exists. Neither
route output grants authority to implement the product or this proposal.
