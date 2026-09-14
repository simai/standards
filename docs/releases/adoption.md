# Adopt the 1.0.0 release

Pin the repository tag `v1.0.0` or its commit and verify `release-manifest.json`
with `python tools/verify_release.py`. Vendor the release or an explicitly reviewed
subset with the license and normative sources; preserve exact dependency hashes.

For AI First use `spec/1.0`, `schemas/1.0`, `tools/aifirst10.py` and its imported
tools. Follow [the reader guide](../1.0/quickstart.md) and [migration guide](../1.0/migration.md).
The stable wire contract is unchanged from 1.0.0-rc.1. Existing candidate
publications need no wire conversion. Historic pilot receipts remain candidate-bound.

For Standard Contract use `standard-contract/1.0/contract.py`, its adjacent schemas
and SPEC.md; the incorporated draft-1 definitions are in `standard-contract/SPEC.md`.
The stable envelope is `formatVersion: "1.0"`. Use the [prompts](../../standard-contract/1.0/PROMPTS.md)
and [lifecycle workflow](../../standard-contract/lifecycle/README.md). Vendor the
whole `standard-contract` directory if migration/lifecycle tools are needed.

Draft-1 migration uses the stable lifecycle `migrate1` command with an explicit
version plan, never the legacy automatic PATCH migrator. For draft-2, retain the
historical reader until a reviewed replacement bundle is prepared: assign new
MAJOR subject versions for the new format, change envelope/project/declaration
versions, recalculate local pins from parents to descendants, then bindings and
sidecars. Compare requirements and resolve every binding with the stable reader.
There is no automatic draft-2 migration command in this release. Do not edit a
published subject version in place. Lifecycle draft records also require explicit
conversion to record version `1.0`; historical evidence does not certify new bytes.

Standards select rules; resolution is not evidence of object conformance. Manual
requirements need review. An update preview/candidate is not automatic approval.
No project is updated by installing this release.

## Message for another AI task

```text
Use the released AI First 1.0.0 and Standard Contract 1.0.0 from ai-first tag
v1.0.0. Read RELEASE-STATUS.md and docs/releases/adoption.md first. Verify the
release inventory, then use spec/1.0 and standard-contract/1.0 as the stable entry
points, with standard-contract/lifecycle for version management. Historical draft
labels under experiments/ and archives/ do not describe these stable editions.
Pin adopted files locally, preserve existing project behavior, and report checks
separately from manual conformance and product acceptance.
```
