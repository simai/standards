# Federation and project handoff: combined stable 1.0.0

Adopt AI First 1.0.0 and Standard Contract 1.0.0 from release tag `v1.0.0`.
Start with [release status](../RELEASE-STATUS.md) and [adoption](../docs/releases/adoption.md).
Verify `release-manifest.json` before vendoring. No automatic federation or project
changes are requested by this document. Existing owners choose their integration batch.

AI First wire version is 1.0. Standard Contract envelope and optional lifecycle
records use 1.0. Stable implementation entry points and CLI examples are in
[Standard Contract](../standard-contract/1.0/README.md) and
[lifecycle](../standard-contract/lifecycle/FEDERATION-HANDOFF.md).

Keep exact local pins and historical handlers. A format transition requires an
explicit version plan and separate output. Never interpret resolution, hash
verification or stable release status as evidence that a product satisfies rules.
Return the source revision, adopted digests, commands/results and unresolved manual
requirements. Docara/Larena 1.0 pilot acceptance is still pending.
