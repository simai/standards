# Governance

## Status and stewardship
AI First 0.1 is a pilot specification maintained in this repository. The project
owner acts as initial editor and acceptance authority. This is not a claim of
multi-organization consensus. Technical discussion and review should be recorded
in issues or pull requests when a public collaboration surface is established.
No organization must adopt SIMAI tooling or products to contribute or implement.

## Change process
1. Open a proposal describing a concrete publisher/reader scenario and failure.
2. Compare existing standards and simpler options before adding wire fields.
3. State compatibility, security, migration, implementation and licensing effects.
4. Supply normative prose, schema changes, valid and invalid examples, and tests.
5. Review the proposal and record objections and the editor's reasoned decision.
6. Merge only after the appropriate review and checks. Publish a changelog and
   explicit version transition; keep prior distributions available.

A rejected or deferred proposal remains a documented decision, not a hidden
implementation requirement. An unresolved normative conflict blocks the affected
release claim. Implementations must not resolve conflicts by silently diverging.

## Version policy
The wire version is 0.1; the initial distribution is 0.1.0. Patch releases may
correct editorial errors and implementation defects while preserving wire meaning.
A breaking change, new required behavior or changed interpretation requires a new
wire version and a migration guide. Optional extensions must obey C01. No client
is expected to guess compatibility with an unknown wire version.

## Maturity progression
- Pilot Specification: complete bounded contract with reproducible first-party
  tooling and examples; suitable for controlled adoption.
- Interoperability Candidate: at least two independently authored readers and
  two independent publishers reproduce the declared scenarios and failure cases.
- Stable Community Specification: the candidate evidence is public, material
  issues are resolved, governance has external participation and compatibility
  commitments have been reviewed.

These are this project's maturity labels. Formal international recognition, if
pursued, follows the chosen standards organization's actual process separately.
No automatic date or test count grants that status.

## Expansion criteria
Search, processes, signatures, federated catalogs and execution adapters require
new demonstrated scenarios and bounded proposals. Preserve static/local use,
ordinary source formats, progressive retrieval and server-enforced authorization.
Before promoting the public name or registering discovery identifiers, review
existing use and relevant registries. File-name collision handling is required now.
