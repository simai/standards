# Federation handoff: Standard Contract draft-2

Status: local experimental implementation ready for integration review.
Owner source: this directory in the AI First repository. Do not create a separately
maintained canonical copy. This handoff does not itself change federation runtime.

## New interfaces

- `standard.schema.json`: draft-2 with file-relative pinned `extends`, addressable
  `uses`, informative `references` and optional `specification`.
- `project.schema.json`: draft-2 project bindings; paths relative to configuration.
- `declaration.schema.json`: adjacent `<object>.standards.json`; paths relative
  to declaration, explicit target/kind/direct standard selection.
- `contract.py resolve PROJECT TARGET [--artifact JSON]` automatically reconciles
  an adjacent declaration with project bindings.
- `contract.py standalone DECLARATION [--artifact JSON]` authorizes only the
  declaration directory as bundle root; no implicit fallback from project errors.
- `contract.py declare PROJECT TARGET [--write]` previews by default and exclusively
  creates the adjacent file when requested.
- `migrate.py OLD_PROJECT [--output NEW_DIRECTORY]` previews or writes a validated
  conversion with missing-information and proposed-version reports.

## Version planning update

For new migrations and dependency updates, use the
[explicit lifecycle workflow](../lifecycle/README.md) and its
[federation handoff](../lifecycle/FEDERATION-HANDOFF.md). It requires explicit target
versions. The automatic PATCH migration documented below is retained only as a
historical interface and is not recommended for new adoption.

## Integration requirements

Dispatch by explicit formatVersion; preserve the draft-1 tool and schemas.
Do not feed draft-1 paths into the draft-2 resolver: their bases differ. Use the
migration command to recalculate paths, versions and digests. It imports the
existing draft-1 resolver, so vendor that dependency with migration tooling.

Keep distinct evidence dimensions: selected standards, local normative-context
availability, and artifact conformance. `available` is scoped to inherited standards
and directly declared contract bytes; arbitrary external protocol graphs are not
traversed. Manual requirements remain needs-review. URL-only uses remains incomplete.
Schema success or an AI statement must not be promoted to product conformance.

Source links never authorize downloading or execution. Root escapes, identity/pin
conflicts and declaration disagreements fail. Informative missing files are visible
but do not add obligations. A declared standard does not replace federation safety,
authority, owner or process contracts.

## Acceptance

Run the commands in [README.md](README.md), demonstrate the three included examples,
and exercise existing draft-1 users through their unchanged handler. Provide the
exact vendored revision, checks, mapping to owner skills and remaining limitations.
Use [PROMPTS.md](PROMPTS.md) for the four user-facing scenarios. Opt-in project
activation remains a separate owner action; do not perform mass conversion.

No public release, product editing, network loader, signatures or stable-version
claim is included. The specification remains [SPEC.md](SPEC.md).
