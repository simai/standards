# Changelog

## 1.1.1 — 2026-11-02

- Reference reconcile (`standards/linkage.py`): a place with an anchor follows
  only that anchor's dependencies and the anchors of a dependency are not
  followed, so a law change marks only the documents that contain the affected
  clause; a norm no longer in force needs action; an edition that took effect
  after the place was made is found when no earlier edition is recorded.
- The two standards stay at 1.1.0; their text is unchanged.

## 1.1.0 — 2026-11-02

- Add `simai.linkage` 1.1.0: a universal core for unit passports, release
  inventories, change reports, usage records and one reconcile, with profiles
  framework (exactly 1.0.0), norms (mirrored law editions) and templates.
- Add `simai.change-lifecycle` 1.1.0: the general half of the Framework change
  lifecycle, with the mirror journal for sources the publisher does not control.
- Add core schemas, byte-identical pins of the Framework formats, the reference
  implementation `standards/linkage.py`, fixtures and tests.
- The repository moves to `simai/standards`. AI First 1.0.0 and Standard
  Contract 1.0.0 are unchanged.

## 1.0.0 — 2026-09-14

- Release AI First 1.0.0 and Standard Contract 1.0.0 together, including the stable
  optional lifecycle profile.
- Preserve historical candidate bytes and draft handlers with explicit verification.
- Add stable adoption entry points, migration guidance and release integrity checks.
- Separate maintainer-supported releases from product pilot and community maturity.
- Reject incomplete verification records in the historical product-backed gate.

Historical changelogs remain in the candidate archives and experimental editions.
