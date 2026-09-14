# Lifecycle verification

Date: 2026-09-14. Status: local stable 1.0.0 acceptance.

The lifecycle suite passes 26 tests covering:

- editorial/minor/major comparisons, uncertain normative prose, separate author
  claims, immutable releases, insufficient categories and replacement history;
- inheritance and usage impact, existing object/sidecar inventory and coverage limits;
- old pins remaining effective despite new proposals;
- new candidate preparation, unchanged sources, rewritten child pins/declarations,
  repeatable output, no object copying and refusal to overwrite;
- missing target versions, occupied versions, contradictory catalog identities,
  stale source inputs, inconsistent declarations and source rechecks;
- draft/active/deprecated/withdrawn/unknown decisions, latest journal decisions and
  historical resolution independently of adoption eligibility;
- evidence applicability for object/rule/checker changes, evidence digest changes,
  explicit non-certification of recorded claims and lifecycle-independent freshness;
- no networking, explicit major-version draft-1 migration, schema correctness and
  real CLI report handling.

The complete example foundation -> documentation children -> project -> page
sidecar transition is exercised in temporary directories. Source snapshots remain
identical. Existing draft-1/1.0 and frozen AI First checks are run separately.

This does not certify arbitrary text semantics, global identity ownership,
authenticity of owner decisions or evidence, product adoption, live upgrade or
cross-client interoperability. Prepared bundles remain candidates requiring review.

Commands are listed in [README.md](README.md). The source of truth is
[SPEC.md](SPEC.md), with typed input schemas beside it.

## Regression results

- Lifecycle profile: 26 tests passed.
- Standard Contract draft-1: 18 tests passed.
- Standard Contract 1.0: 26 tests passed.
- Main AI First repository suite: 140 tests passed with the configured Node runtime.
- Repository English-source, links and root inventory checks: passed.
- Frozen AI First 0.2: 101 pinned files verified unchanged.
- Frozen AI First 1.0: 63 pinned files verified unchanged.

Total across these four test suites: 210 passing tests.
