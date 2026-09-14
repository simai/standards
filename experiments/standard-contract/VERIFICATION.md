# Local verification

Date: 2026-09-14. Status: passed within the experimental scope.

- 18 contract tests passed using the repository Python environment.
- API and tutorial bindings resolve to their distinct profiles and shared parent.
- Component usage does not inherit utility implementation rules.
- Repeated resolution and checking preserve inputs and produce equal output.
- Changed digests, conflicting values and identity/content conflicts fail.
- Missing binding, invalid paths, escaped symlinks, unknown verification methods
  and duplicate JSON keys fail.
- All example standards and project bindings validate against their schemas.
- The example artifact passes two mechanical checks and reports two manual
  checks as `needs-review`; it is not falsely reported as fully conforming.
- Repository documentation, language and inventory checks pass.
- Frozen AI First 0.2 and 1.0 candidate verifiers pass unchanged (101 and 63 files).

No product integration, AI authoring run, independent client, arbitrary-prose
conflict detection or generator idempotence has been demonstrated. The existing
AI First stable-promotion goal remains separate and blocked on product receipts.

Reproduce with the commands in the adoption guide. This evidence records local
behavior and does not assert international standardization or complete domain
conformance.
