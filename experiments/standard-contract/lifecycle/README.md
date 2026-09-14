# Standard Contract lifecycle

A separate experimental profile for version comparison, requirement history,
local impact analysis, explicitly versioned candidate preparation and evidence
applicability. Start with the example commands; read [SPEC.md](SPEC.md) for the
rules and [PROMPTS.md](PROMPTS.md) for instructions to give an AI.

This does not introduce a new standard envelope: draft-2 remains the base format.
The new external record edition is `lifecycle-draft-1`.

## Compare and inspect

From the repository root, with its Python environment and `jsonschema` dependency:

```sh
.venv/bin/python experiments/standard-contract/lifecycle/lifecycle.py compare \
  experiments/standard-contract/lifecycle/examples/project/standards/docs.foundation.json \
  experiments/standard-contract/lifecycle/examples/project/proposals/patch/standard.json \
  --transition experiments/standard-contract/lifecycle/examples/project/proposals/patch/transition.json

.venv/bin/python experiments/standard-contract/lifecycle/lifecycle.py impact \
  experiments/standard-contract/lifecycle/examples/project/project.json docs.foundation
```

`proposals/minor` adds a recommendation; `proposals/major` adds a mandatory rule.
The PATCH example changes presentation and the specification link's relative
spelling; the comparator conservatively asks for review of that reference change.
No author's compatible claim overrides the independent result.

Impact includes the API/tutorial children, their prefixes, actual pages and the
API page declaration. It reports excluded paths and does not know external users.
Existing bindings still select 1.0.0 even while later proposals exist on disk.

## Prepare a new bundle

```sh
.venv/bin/python experiments/standard-contract/lifecycle/lifecycle.py prepare \
  experiments/standard-contract/lifecycle/examples/project/project.json \
  experiments/standard-contract/lifecycle/examples/project/update-plan.json \
  experiments/standard-contract/lifecycle/examples/project/release-catalog.json
```

This is a preview. To create a candidate, repeat with
`--output /tmp/standard-contract-lifecycle-candidate`, choosing an absent directory
outside the source project. Include `--journal PATH` to report lifecycle decisions.

The example explicitly assigns 1.0.1 to the foundation and both documentation
children. Omit a child's targetVersion and preparation fails. The new bundle
contains standards, required materials, project configuration, prepared sidecars
and `lifecycle-report.json`. It does not contain transformed pages or business code.
Resolve the generated configuration with the draft-2 reader before introducing
objects and running domain checks. `newAdoptionReady` remains false until a separate
owner acceptance process; building a candidate is not deployment or release.

The source plan binds the project digest and each changed standard's old identity
and digest. Supply exact target versions. A replacement path is relative to the
plan and confined to the project; its internal links are file-relative. The local
release catalog lists known occupied versions. Collision checks are local, not a
claim that a namespace is globally free.

## Record lifecycle decisions

`journal.json` illustrates append-only owner-attributed decisions. Use:

```sh
.venv/bin/python experiments/standard-contract/lifecycle/lifecycle.py status \
  experiments/standard-contract/lifecycle/examples/project/standards/docs.foundation.json \
  --journal experiments/standard-contract/lifecycle/examples/project/journal.json
```

No journal means unknown. Deprecated warns; withdrawn prevents new adoption
eligibility but does not destroy the historic standard or stop pinned resolution.
A decision source is attribution, not an authenticated signature.

## Check old evidence

```sh
.venv/bin/python experiments/standard-contract/lifecycle/lifecycle.py evidence-check \
  experiments/standard-contract/lifecycle/examples/project/project.json docs/api/button.md \
  experiments/standard-contract/lifecycle/examples/project/page-evidence.json \
  --checker-id example.review --checker-version 1.0.0
```

The example record is current but all requirements are not-checked. Use
`evidence-template PROJECT TARGET --checker-id ID --checker-version VERSION` to
emit a new template to stdout. Fill results only after actual checks; pass/fail
requires local hashed evidence files relative to the receipt's directory.

Changing a page, its normative inputs, evidence bytes or expected checker version
makes a receipt stale. It is never silently rebound. Matching hashes establish
applicability, not the truth of a prose claim or suitability of its evidence.

## Migrate the envelope explicitly

Use `migrate1 OLD_PROJECT PLAN CATALOG [--output NEW_DIRECTORY]` through this CLI.
The plan uses the same schema: provide the old project digest and one source pin
plus explicit targetVersion for every reachable standard. Do not provide content
replacements in a format-only migration. This profile requires a MAJOR change
because the source envelope reader cannot read draft-2. Missing usage locations
remain listed in the report. Sources and objects are not rewritten.

The older `draft-2/migrate.py` is retained for historical users. Its automatic
PATCH proposal is not recommended for new work. Use the lifecycle command instead.

## Owner procedure

1. Preserve a released revision and reserve the next explicit identity/version.
2. Compare requirements and record a transition with rationale, replacements and
   required checks. Resolve semantic questions with subject-matter evidence.
3. Inspect local impact and name any external/uninspected areas.
4. Prepare a new bundle using a complete plan and known release catalog.
5. Introduce object copies separately, perform domain checks, create new evidence
   and review lifecycle eligibility. Preserve existing releases and receipts.
6. Activate or publish only through the owner's separately authorized process.

For project use, vendor the lifecycle directory plus sibling draft-2 tool/schemas.
Explicit draft-1 migration also requires the original draft-1 reader/schema. All
these files remain authored in AI First; generated copies must not become competing
canonical specifications. The repository license applies.

## Verify

```sh
.venv/bin/python -m unittest discover -s experiments/standard-contract/lifecycle -p 'test_*.py'
.venv/bin/python -m unittest discover -s experiments/standard-contract/draft-2 -p 'test_*.py'
.venv/bin/python -m unittest discover -s experiments/standard-contract -p 'test_*.py'
.venv/bin/python tools/check_candidate02.py
.venv/bin/python tools/check_candidate10.py
.venv/bin/python tools/check_repository.py
```

See [VERIFICATION.md](VERIFICATION.md) for the acceptance evidence and
[FEDERATION-HANDOFF.md](FEDERATION-HANDOFF.md) for integration.
