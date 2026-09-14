# Road to AI First 1.0

Status: active development direction requested on 2026-09-12. This document
sets the stable-version target; it does not declare a 1.0 release, accept a new
wire profile or revise the frozen 0.2 candidate.

## What 1.0 means for this project

A publisher and client implementer can rely on a clearly bounded contract,
reproducible examples, stated compatibility rules and tested migration. A small
site remains useful with the minimal resource envelope. Service composition,
scenario assessment and domain compatibility remain optional descriptions or
adapters unless experiments prove a reusable semantic gap.

1.0 is a stability commitment, not proof of universal completeness, international
recognition or support by every model. Versions after 1.0 are expected: fixes and
compatible additions continue without making 1.0 an unfinished release. These are
our planned compatibility rules, to be ratified with the stable specification:

| Change | Planned release treatment |
| --- | --- |
| Editorial correction with unchanged normative meaning | Patch; document the correction and tests affected. |
| Compatible optional capability that old clients may safely ignore | Minor; preserve existing meaning and publish support requirements. |
| Changed meaning, removed behavior or incompatible required fields | Major; explicit migration and parallel old-reader support. |
| Candidate before stable acceptance | Release candidate such as 1.0.0-rc.1; never labelled stable merely to change appearance. |

Distribution version, wire version and optional profile revisions must be clearly
separated. Existing 0.1/0.2 readers reject unknown wire versions. Consequently a
1.0 wire identifier cannot be introduced by renaming VERSION alone: new dispatch,
schemas, migration, fixtures and compatibility documentation must ship together.
We do not need intervening 0.3 through 0.9 releases before a justified 1.0.

## Current progress

- Frozen 0.2.0-rc.1 remains unchanged and hash-verifiable.
- The [development-directions plan](../proposals/2026-09-12-larena-development-directions-review.md)
  is now being executed for isolated experiments; its earlier review text remains
  a historical proposal record.
- [Runnable experiments](../../experiments/development-directions/README.md)
  demonstrate existing-wire delivery of descriptions plus a synthetic domain
  adapter, with zero new required fields and zero new profiles.
- Current Docara/Larena result receipts are still needed for the previously
  agreed product acceptance. Synthetic fixtures cannot stand in for those pilots.

## Delivery sequence and exit criteria

| Stage | Output | Exit evidence |
| --- | --- | --- |
| A. Execute composition/scenario/compatibility experiments | Linked materials, domain adapter, fixed cases and negative evidence cases | Existing reader retrieves complete descriptions; hidden/missing/unavailable distinctions; all assertions reproducible; no frozen-file change. |
| B. Decide smallest stable scope | Explicit keep/clarify/defer decisions; no arbitrary expansion of core | Two deployment shapes and another domain demonstrate reuse, or a concrete extension gap is recorded. Unsupported-client behavior defined before accepting any profile. |
| C. Prepare self-contained 1.0 specification | Normative core and optional profiles without requiring readers to mentally merge 0.1 and 0.2 prose; 1.0 schemas and dispatch, migration and examples | Requirement-to-prose/schema/tool/test trace; old versions retain exact meaning; migration writes new outputs. Any new semantics require an explicit decision. |
| D. Verify clients and publication experience | Fixed conformance corpus, Python/JS advertised support matrix, actual product pilot evidence | No skipped requirement represented as pass; negative access/URL/cache/revision cases; baseline and benchmark reproduced. |
| E. Freeze 1.0 candidate and accept locally | Immutable file lock, compatibility policy, changelog, adoption/maintenance guide | Reviewed defects resolved or excluded explicitly; applicable pilots accepted; reproducible release candidate. |
| F. Stable 1.0 and external distribution | Versioned stable package and discussion materials | Stable acceptance recorded; public release/outreach needs its separately authorized action. |

Stages A–C can make progress independently of pending product artifacts. Stage D
cannot claim real product evidence without returned builds and scenario results.
Missing external artifacts must be reported without restarting already completed
local checks. Publishing the release is a separate action from preparing it.

## Scope decisions supported by the first experiment

Keep the existing small envelope. Use knowledge materials to carry compositions
and scenario descriptions. Their domain interpretation currently requires a
separate adapter; we must not present it as generic client interoperability.

Keep deterministic comparison and permission decisions outside LLM reasoning.
Do not standardize an executable scenario language, a universal compatibility
language, a live service registry or mandatory signatures for 1.0. Consider only
minimal typed references/evidence bindings after a second domain and client prove
that a shared convention removes project-specific interpretation.

## Evidence still required before stable release

The second domain and independent interpretation check are complete. Actor-
filtered HTTP publication tests (including error/provenance/cache disclosure),
reproducible real Docara/Larena results, and the current federation process
acceptance gaps remain. They must stay visible instead of being represented as
completed product evidence.
