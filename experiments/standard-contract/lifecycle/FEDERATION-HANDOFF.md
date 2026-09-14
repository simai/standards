# Federation handoff: Standard Contract lifecycle

Edition: lifecycle-draft-1, experimental. Canonical source: this directory in
AI First. This is an optional profile above unchanged draft-2, not a replacement
for federation authority, process, safety or owner contracts.

## Interfaces

Use `lifecycle.py` commands: `compare`, `impact`, `prepare`, `migrate1`, `status`,
`evidence-template`, `evidence-check`. See [README.md](README.md) for arguments.
Five external schemas define transition, plan, catalog, journal and evidence.
Vendor sibling draft-2 dependencies; explicit draft-1 migration also needs the
original reader/schema. Preserve old dispatch and entry points for historical use.

New work must use explicit version plans. Stop recommending the old draft-2
migrator's automatic PATCH increments. Format migration and normative requirement
changes have independent compatibility consequences; compare both.

## Required semantics

- Exact versions and immutable bytes; no automatic latest or mass project upgrade.
- Report author claims separately from compatibility evidence.
- Candidate preparation writes an absent directory, never the live project.
- Rewritten children need explicit new versions; collision scope is local.
- Lifecycle status, technical conformance and evidence applicability are distinct.
- Missing journal means unknown; withdrawn blocks new adoption eligibility while
  preserving historical resolution. Status decisions are not authenticated here.
- Hash-matching evidence is applicable, not automatically semantically verified.
- Preserve coverage limits and unresolved normative context in user-facing results.

## Acceptance

Run all three Standard Contract suites and AI First integrity checks from the
usage guide. Demonstrate the foundation -> documentation child -> project binding
-> page declaration chain using the included project and explicit update plan.
Return exact vendored revision, commands/results, owner integration mapping and
remaining limitations. Refer to [VERIFICATION.md](VERIFICATION.md).

Use [PROMPTS.md](PROMPTS.md) for user-facing workflows. Activation in product
projects, public releases, network loading and a global registry are separate work.
This handoff is a file for the user to transfer; no federation task was messaged.
