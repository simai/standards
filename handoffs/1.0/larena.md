# Larena pilot handoff — AI First 1.0.0-rc.1

Status: prepared for the existing Larena executor. No task has been created or
message sent. The user transfers this file link when it fits the product plan.

Candidate: `1.0.0-rc.1`; wire version: `1.0`.
Candidate lock SHA-256: `1a5010469988a9fcdaf76799e30897130e62cc16a821933109d67a160655aab3`.
The [candidate inventory](../../conformance/1.0/candidate.json) pins each contract,
schema and tool. Run `python tools/check_candidate10.py` before integration.
A mismatch requires a new candidate from the standard owner, not a local override.

## Outcome and ownership

A client can discover Larena documentation and the existing `setting.site.read`
capability, determine the relevant access constraints, and locate its authoritative
contract. The AI First reader must not call the business handler.
The existing Larena executor owns planning and product implementation; ai-first
owns the standard and compatibility review. Keep the current product plan and
ownership intact. No new executor, production change or public release is requested.

## Reuse existing contracts

Inspect the current operation registry, OpenAPI generator and Access mechanisms
before implementing. Derive exported facts from them; do not hand-copy input/output
schemas or authorization rules into another registry. Previously observed names
are starting points, not proof of the current checkout's state.

First determine whether `setting.site.read` has an existing HTTP operation and an
OpenAPI operation locator. If present, publish a capability descriptor linking to
that existing JSON/YAML contract and its real JSON Pointer. Use the existing source
of truth for effect and access metadata; unknown information stays `unknown`.

If there is no HTTP contract, record that fact and describe the existing internal
contract using an `external` locator plus its required explanation and usage
instructions. **Do not create a new business endpoint for this pilot.** An external
binding's result is `not-run`, not a falsely passed OpenAPI operation check. This
branch is a valid product outcome if it accurately represents the actual product.

See the [service example](../../examples/1.0/service/ai.json) for the wire shape
only; its sample operation is unrelated to Larena and must not be reused as a real
endpoint. The [core](../../spec/1.0/core.md) and
[publishing guide](../../docs/1.0/publishing.md) define access hints,
OpenAPI versions, separate credentials and local validation.

## Publication and access boundary

Generate documentation descriptors and full readable materials from existing
product sources. Access metadata describes the existing mechanism; it never carries
a token, cookie, secret, credential or authorization grant. Keep any test credentials
outside the manifest and returned bundle. Exercise existing Access logic with local
synthetic principals and organizations. Do not invoke the advertised business handler
as a way to demonstrate the reader.

For offline compatibility, provide sanitized local publication fixtures. For
protected HTTP behavior, provide a reproducible local test/server configuration
and redacted actor-specific evidence. The ai-first owner reviews it before running
product commands. If denied responses cannot be represented as offline files, say
so: a static snapshot cannot prove live authorization behavior.

## Acceptance scenarios

| Receipt scenario ID | Required evidence |
| --- | --- |
| `documentation` | Reader discovers a local publication and reads named documentation with exact revision/version/language and source attribution. |
| `operation-binding` | Existing registry identity `setting.site.read` maps to its real OpenAPI locator, or a documented internal-contract branch demonstrates that no HTTP operation exists. |
| `guest` | Observed guest visibility/read behavior matches existing Access policy; do not assume guest denial or permission. |
| `allowed-user` | A permitted synthetic user reads the appropriate protected publication/descriptor through existing access mechanisms. |
| `denied-user` | A user without permission receives the existing denied behavior and no protected documentation from another principal's cache. |
| `other-organization` | A synthetic user from another organization cannot obtain tenant-protected material; no cross-organization fallback. |
| `no-business-execution` | Instrumentation/test spy proves the standard reader never invoked the advertised business handler. |
| `access-isolation` | Credential scope and cache isolation hold across actors and organizations, including denied responses. |

An actor scenario passes when behavior matches the existing policy, not when a
particular HTTP status is forced to satisfy this handoff. If the product lacks the
necessary documentation-access surface, report a blocker or bounded product proposal
instead of changing business APIs. Internal Access unit tests are useful evidence
but are not automatically proof of the complete protected HTTP path.

## Required checks and return package

Run applicable product tests, local fixtures and the ai-first reader against the
returned publication. Record exact commands rather than these placeholders:

```sh
python tools/check_candidate10.py
python tools/aifirst10.py validate /path/to/local/publication
python tools/aifirst10.py list /path/to/local/publication --kind capability
```

The JavaScript baseline intentionally does not validate capability contracts or
protected access. Use Python for those checks; do not label a skipped JS capability
check as a pass.

Return `pilot-result.json` using the [result schema](../../schemas/1.0/pilot-result.schema.json)
with product `larena`, the exact candidate/lock digest, full product code revision,
environment, commands/exit codes, redacted evidence, relative publication paths,
SHA-256 artifact inventory, every scenario ID above and all limitations.
Set `businessExecution` to `not-run`. Include the observed registry/OpenAPI evidence
for either operation-binding branch and explicit actor/organization test results.

The return inspector verifies artifact integrity and publication compatibility.
Scenario claims still require review and reproducibility; a schema-valid JSON report
is not automatically an accepted pilot. No actual product result is attached here.

## Escalation and revision policy

Return contradictions with a minimized fixture, expected/actual behavior, scenario
ID, contract hash and whether the defect appears to belong to the standard or
integration. Do not fork the format or invent a missing HTTP contract. A changed
standard contract gets a new candidate/lock and an updated handoff for the user
to forward. No messages to product chats are authorized by this handoff.
