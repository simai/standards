# Docara pilot handoff — AI First 1.0.0-rc.1

Status: prepared for the existing Docara executor. No task has been created or
message sent. The user transfers this file link when it fits the product plan.

Candidate: `1.0.0-rc.1`; wire version: `1.0`.
Candidate lock SHA-256: `1a5010469988a9fcdaf76799e30897130e62cc16a821933109d67a160655aab3`.
The [candidate inventory](../../conformance/1.0/candidate.json) contains exact
per-file hashes for the contract, inherited requirements, schemas and tools.
Run `python tools/check_candidate10.py` in the ai-first checkout before adoption.
Any mismatch stops integration until the standard owner issues a new candidate.

## Outcome and ownership

Enable an AI client to find the correct Docara documentation version/language,
read complete examples, cite the source and detect stale or incomplete output.
The existing Docara executor owns scheduling, code, tests and product decisions.
The ai-first task owns the standard and compatibility review. Do not displace
unfinished product work or create another executor for this pilot.

## Integration scope

Use the current build pipeline and Document IR as the source of truth. Verify
the actual current classes/extension points in the checkout before changing them;
previous architecture descriptions are guidance, not a claim about current code.
Generate AI First descriptors, catalogs and full text from the same material as
the site. Existing projects must explicitly opt in. An absent setting preserves
current output behavior. Do not introduce a parallel content authoring format.

The first fixture is actual public Docara documentation built locally. The second
is a small isolated two-language fixture with exact product versions. All pilot
outputs are local, using public documentation or synthetic data. No production
change, public release, external outreach or business operation is authorized.

## Inputs and expected outputs

Inputs: existing Document IR, source/page IDs, titles, descriptions, locale,
explicit product version, source URL, current renderer and build configuration.
Do not infer translation equivalence from a matching title. Supply a reviewed
language-neutral translation identity only where the source model provides one.

Outputs: `ai.json`, optional pinned catalogs, full Markdown/plain representations,
and optional generated llms.txt, all inside the existing build output contract.
Representation bytes must preserve fenced code and table content. For a complex
component, use its semantic source/IR or emit a documented unavailable/failure
condition; silently dropping important content is unacceptable. Child revisions
and digest pins must agree. Removed pages must disappear from all generated indexes.

Use the [minimal publication](../../examples/1.0/minimal/ai.json),
[joint-export example](../../examples/1.0/joint-export/ai.json),
[publishing guide](../../docs/1.0/publishing.md),
[core contract](../../spec/1.0/core.md) and
[transport contract](../../spec/1.0/discovery-and-transport.md).
These are protocol examples, not mandatory Docara directory layouts.

## Acceptance scenarios

| Receipt scenario ID | Required evidence |
| --- | --- |
| `opt-in` | Existing project without the option behaves as before; explicitly enabled project emits the export. |
| `real-docs` | Build the actual public Docara documentation locally; reader selects and reads named real pages with source attribution. |
| `multilingual` | Isolated two-language fixture: exact language/version, explicit fallback policy, no accidental cross-version substitution. |
| `code-tables-components` | Before/after source and representation samples for code, tables and complex components; relevant content retained or explicitly reported unavailable. |
| `full-build` | Full build produces a valid publication and deterministic output on unchanged input. |
| `single-page-build` | A one-page rebuild updates the relevant export and ancestors; unaffected catalogs retain revisions/digests. |
| `page-deletion` | Deleting a fixture page removes stale catalog/llms entries and stale exported material through the product's own output mechanism. |
| `error-preserves-output` | Inject a build/export failure; previous usable output remains byte-identical and no mixed snapshot is published. |
| `joint-export` | AI First and llms.txt derive from the same records/text; no second hand-maintained inventory. |

At minimum run the product's applicable build/tests and, from ai-first:

```sh
python tools/check_candidate10.py
python tools/aifirst10.py validate /path/to/local/export
python tools/aifirst10.py read /path/to/local/export --id urn:fixture:chosen-item
node tools/aifirst10.mjs read /path/to/local/export --id urn:fixture:chosen-item
```

The paths/ID above are placeholders: substitute actual local artifacts and item
IDs and record the exact commands. Do not mark a command passed merely because
an illustrative command appears here. Full routed publications require separate
inventory validation. Measure publication maintenance effort as observed changes,
commands and actual time if recorded; do not estimate hours retroactively.

## Return package

Return a local bundle and `pilot-result.json` conforming to the
[result schema](../../schemas/1.0/pilot-result.schema.json):

- Product `docara`, exact candidate/lock digest and full product code revision.
- Runtime/dependency versions, reproducible build instructions and exact commands,
  exit codes and sanitized logs.
- Relative publication manifest paths and a complete SHA-256 inventory of files
  needed by the reader, plus the scenario evidence.
- One result for every scenario ID above, with evidence paths and limitations.
- `businessExecution: "not-run"`. Do not include credentials or private raw logs.

All artifact paths are relative to the bundle, never host-specific paths. Preserve
before/after manifests and the error-injection proof. The return inspector checks
receipt integrity and publication compatibility, then leaves scenario acceptance
pending review; its exit code alone does not certify the whole product pilot.

## Contradictions and changes

If an existing build boundary conflicts with this contract, return the exact
scenario, minimized input, expected/actual behavior, candidate hash and suggested
standard or product fix. Do not silently fork the wire format. Contract changes
require a new candidate ID and lock; the standard owner updates this handoff and
the user forwards the revision. No chat notification is assumed or sent here.
