# simai.linkage 1.1.0 — universal core, draft for the owner's review

Date: 2026-11-02. Status: **approved by the owner** (revision 2, 2026-11-02),
pending the Framework thread's second review and the change-lifecycle split.
Nothing here changes a published standard, a schema or a pin until it is
published in `simai/standards`.

Owner direction of 2026-11-02: the linkage standard becomes universal and its
core lives with Standard Contract in this repository, which becomes
`simai/standards`. SIMAI Framework keeps its own
rules as a profile. The first non-Framework users are the norm registry, the
document templates and the client documents of `mirai-documents`.

**Source.** `simai.linkage` 1.0.0, `ui-source/contracts/standards/simai.linkage/1.0.0/standard.json`
(approved 2026-10-27, owner `simai/ui-source`). Every 1.0.0 requirement is kept.
What was Framework-specific (kinds, id grammar, how the hash is taken, the
semver-only version, the impact rule, how files map to units) moves to the
Framework profile without change, so every passport, inventory and change report
written under 1.0.0 stays valid and no Framework file has to change.

Revision 2 (same day) applies the Framework thread's review
(ui-control `control/evidence/2026-11-02-simai-linkage-universal-draft-review.md`,
commit bdd0f1f): seven Framework requirements had been weakened in restating and
six core requirements would have been new for the Framework. Both are corrected
below; the new requirements are scoped to the profiles that need them.

## Why 1.0.0 is not enough outside the Framework

Applied to laws, templates and contracts (see `mirai-documents/docs/STANDARD.md`),
1.0.0 fits in shape — a passport, an inventory, a change report, a usage record,
one reconcile, foundations followed through the chain — but not in five details:

1. **Versions.** A law has dated editions, not `major.minor.patch`; a dependency
   is "the edition in force on a date", not a caret range.
2. **Time.** An edition takes effect on a date, may be announced in advance and
   may be repealed. A contract signed under the old edition stays valid. 1.0.0
   has no effective dates and no "reconcile as of a date".
3. **Content outside git.** The text of a norm comes from an official source,
   not from committed files.
4. **Granularity.** A template clause depends on one article; 1.0.0 tracks whole
   units only.
5. **Impact.** Whether a change needs action depends on how the place uses the
   unit (relies on it, restates it, deviates from it) and on the unit's force
   (mandatory or default). 1.0.0 decides from the version alone.

## Terms

As in 1.0.0 — **unit**, **passport**, **source**, **release**, **inventory**,
**change report**, **consumer**, **usage record**, **place**, **reconcile** — plus:

- **Profile** — the rules of one kind of source: which kinds of units it has, the
  id grammar, the version scheme, how the content hash is taken, how impact is
  decided. `framework`, `norms`, `templates` are the first three.
- **Anchor** — a named part inside a unit that others can point to or that can
  depend on something by itself: a clause of a template, a slot of a component.
- **Edition** — a version under the `dated` scheme: the date it takes effect and
  the act or record that introduced it.

## Core requirements

### Identity and passport

1. **every-unit-has-a-passport** (must, unchanged). Every unit a source publishes
   has a passport: a stable id, a version, its owner and what it is made of. A
   unit without a passport is not published; every content file of a source
   belongs to exactly one unit (the profile says how files map to units).
2. **profile-declared** (must, new). Every passport, inventory and change report
   names its profile and the profile's version, or implies it by a
   profile-specific `schema` id: the Framework's `simai.framework.*` ids imply
   `framework` 1.0.0. A reader that does not know the profile still reads the
   core fields and says it cannot judge the rest.
3. **id-grammar-by-profile** (must, generalized). An id is `<kind>.<name>` in the
   Framework profile; another profile may use `/` paths (`ru/gk/810`,
   `ru/loan`). Ids are unique within a source. In core formats a unit of another
   source is named `<source>:<id>`; the Framework profile names cross-source
   dependencies by bare id, resolved through the inventory's pinned release.
4. **id-never-changes** (must, unchanged). Never reused or silently renamed; a
   rename or renumbering is a new id plus `former_ids` with its journal record.
5. **content-hash** (must, generalized). One SHA-256 over the unit's content.
   The profile names the method: `git-files` (1.0.0: sorted committed files,
   path, zero, length, zero, bytes) or `normalized-text` (text fetched from a
   named source at a recorded time, normalized by the profile's published rule).
6. **version-scheme-by-profile** (must, generalized). `semver` (1.0.0 meaning:
   patch changes no public surface, minor adds without breaking, major needs a
   consumer's action; the profile defines the public surface),
   `dated` (an edition: `since` date and `by` record) or `sequence` (an integer
   that only grows). The scheme decides what "newer" means.
7. **hash-moves-version** (must, unchanged). If the content hash changes, the
   version changes; the release gate refuses otherwise.
8. **dependencies-declared** (must, generalized). A dependency names the unit and
   a constraint in the profile's scheme: a caret range (`range: ^1.2.0`),
   `in-force` (the edition in force on the reference date) or `exact` —
   including the shared foundations a unit reads. A dependency the content uses
   but the passport omits is a defect found by a check, not by a consumer.
   Optional fields where the profile has them: `from` (the anchor that depends;
   absent means the whole unit) and `relation` (from the profile's list, e.g.
   `relies`, `restates`, `details`, `deviates`; the Framework has one implicit
   relation).
9. **anchors-declared** (should, new). A unit that others depend on in part, or
   whose parts depend on different units, lists its anchors with stable ids
   under the same never-reuse rule.
10. **force-declared** (may, new). A unit may state its force for consumers:
    `mandatory`, `default` (consumers may deviate) or `mixed`. Profiles use it in
    their impact rule.

### Sources the publisher does not control

A. **mirror-source** (must for such a source, new). When the units come from a
   source that publishes no passports itself (a legislature, a vendor's API, a
   third-party library), whoever keeps the passports is the **mirror**: it is
   named as the owner, each passport records where and when the content was
   taken (`origin`, `retrieved_at`), and versions follow rule 14 whatever the
   hash method. The mirror never claims to be the source.

### Time (profiles with the `dated` scheme, or that opt in)

11. **effective-dates** (must for `dated`, may otherwise, new). A version may carry
    `effective_from`, `effective_to` and `announced`. A version whose
    `effective_from` is in the future is published in the inventory as upcoming.
12. **reconcile-as-of** (must, new). Reconcile takes a reference date (today by
    default). A place is judged against the version in force on that date; a
    later version already announced is reported as `upcoming`.
13. **valid-under-its-version** (must, new). A place may be marked as made under a
    version on purpose — a signed contract, a shipped release. Reconcile then
    reports `kept` with the newer version, not an error; the place is re-judged
    only when it is changed or re-issued.

### Verification

14. **candidate-then-confirmed** (must for units hashed by `normalized-text`, new). A version found by an automatic
    check of a source (a changed hash of an official text) enters the inventory
    as `candidate` with what found it; a person or a stated rule confirms it.
    Reconcile reports places affected by a candidate as `unverified`, not
    `action-needed`.
15. **unverified-is-visible** (must for units hashed by `normalized-text`, new). A unit whose versions were never
    compared with its source says so (`checked` absent); reconcile shows it, a
    gate may refuse it.

### Inventory and change report

16. **inventory-per-release** (must, unchanged). For the `dated` scheme a release
    is a dated snapshot of the registry.
17. **inventory-is-complete** (must, unchanged).
18. **inventories-compare** (must, unchanged), with anchors: a changed unit lists
    the anchors whose content or dependencies changed.
19. **journal-per-version** (must, unchanged). The entry is data and, for a
    minor or major, says what a consumer does about it (the core journal record;
    the Framework profile uses `simai.change-lifecycle` 1.0.0 until that standard
    is split, see below). For a law edition: what changed, quoted from the
    amending act.

### Consumers and reconcile

20. **consumer-keeps-a-record** (must, generalized). The record names the source
    and release it was last brought up to. For each place: unit id,
    version, content hash, and optionally the anchor, the relation and the
    reference date it was made on. A document passport of `mirai-documents` is
    a usage record.
21. **record-is-local-data** (must, unchanged).
22. **foundations-count / chains-are-followed** (must, generalizes 1.0.0). Within
    a source, reconcile follows declared dependencies: a place that uses a unit
    also depends on its foundations, so a changed colour token marks every place
    drawn with it even when no component version moved. Across sources, a
    consumer may itself be a source (templates use norms; contracts use templates).
    Reconcile follows the chain and every status names its path:
    `ru/gk/809 → ru/loan@1.1.0#interest.rate → contract 15/2026`.
23. **one-reconcile** (must, extended statuses). Each place gets one status:
    `current`, `update-available`, `action-needed`, `former-name`, `missing`
    (1.0.0), plus `upcoming`, `kept`, `unverified`. The profile's impact rule
    decides between `update-available` and `action-needed` from the version
    step, the relation and the force (e.g. `norms`: a new edition of a
    `mandatory` unit that a place `deviates` from is `action-needed`).
24. **report-is-data** (must, unchanged). Never changes the consumer on its own.
25. **no-silent-drift** (should, unchanged).

### Process

26. **gate-in-the-release** (must, unchanged).
27. **one-format-for-all-sources** (must, generalized). All profiles share the
    core formats `simai.unit-passport`, `simai.unit-inventory`,
    `simai.unit-change-report`, `simai.usage-record`, `simai.reconcile-report`
    (`schema_version` 1). The Framework's `simai.framework.*` 1.0.0 formats —
    used by simai/ui-source, simai/ui-pro and any component package — are the
    Framework profile's formats, read as the core formats with the profile
    implied by `schema`. The core mapping names their fields: `range`,
    `includes`, `files`, `former_ids`, `manual`, `step`,
    `dependencies_changed.moved`, violation codes `hash-moved-without-version`,
    `version-went-back`, `source-differs`.
28. **adopt-in-place** (should, unchanged). A norm registry, a template's own
    `template.yaml` and a document passport are extended, not replaced.

## Profiles

| | framework | norms | templates |
|---|---|---|---|
| Owner | simai/ui-source, simai/ui-pro, any component package (`simai.component-package`) | the document library as mirror (A) | the document library |
| Kinds | component, utility, plugin, smart, port, tokens, font, icons, module, core | act, norm | template, block, concept |
| Id | `component.radio` | `ru/gk/810` | `ru/loan`, `ru/common/disputes` |
| Version | semver | dated (`since`, `by`) | semver |
| Hash | git-files | normalized-text | git-files |
| Anchors | slots, CSS variables (later) | parts of an article (later) | clauses `[id: …]`, sections `{#…}` |
| Force | — | imperative → mandatory, dispositive → default | — |
| Relations | — (one, implicit) | — | relies, restates, details, deviates |
| Units to files | a folder `passport.json`, or a central passport under `src/core/passports` whose `includes` claims files or whole folders (component folders included); longest claim wins, an equal claim is a defect | one norm per entry of `norms/<act>.yaml` | a template folder; a shared block file |
| Semver surface | attributes, properties, events, slots, CSS variables, tokens, words, port intents | — | parameters, options, fields, parties, clause ids, checks |
| Impact | major, or a journal entry asking for a change → action-needed with the instruction quoted; former name with its stop date | new edition of a `mandatory` norm a place `deviates` from or `restates` → action-needed; of a `default` norm → update-available | major → action-needed; minor or patch → update-available |
| Constraint | caret range (`^x.y.z`) | in-force | caret range |
| Release id | pair `ui-<12>`; package `pro-<12>` (`larena-<12>` a dated alias until 2027-01-01) | dated snapshot | `<name>-<12>` |
| Formats | the three pinned schemas of ui-source by sha256 | core formats | core formats |
| Consumers | Figma kit, docs, products | templates | client documents (document passport) |

The Framework profile is exactly 1.0.0. Core requirements 2 and 3 (cross-source
naming), 9, 11–15 and A do not apply to it: its profile is read from `schema`
(`simai.framework.*` means `framework` 1.0.0), its anchors and force are absent,
its versions are checked by construction (`git-files`). Its reconcile reports the
five 1.0.0 statuses; nothing new is written by a source or read by its reconcile. The profile follows ui-source as it
stands, including central passports claiming whole folders (ui-source 2aa281a7);
the 1.0.0 guidance text on that point is out of date and is not frozen here.

## Related standards that could move to simai/standards the same way

Reviewed: the ten Framework standards in `ui-source/contracts/standards`.

- **simai.change-lifecycle** — split, before or with linkage 1.1.0. The general
  half (two dated stages, append-only journal, machine-applicable records,
  upgrade from the journal, no undated state) goes to the core; the calendar
  (`lifecycle-policy.json`, compat period, sweep day), the interface-only kinds
  and rewrites, `SF.deprecations.list()`, the alias-table test and
  `sf-upgrade.mjs` stay in the Framework. Otherwise the universal core would
  depend on a Framework standard. Must be reconciled with Standard Contract
  lifecycle, which covers the standards' own versions.
- **simai.ai-development** — stays in the Framework; no ai-first copy. About half
  its rules are Framework-bound; the general half is already the Federation
  working rules, which it references.
- **simai.composite-host-port** — the port idea (declared, separately versioned,
  closed schemas, answered intents, negotiated capabilities, a transport-neutral
  conformance kit) is general, but it extends the composite standards by
  digest. A second wave: extract a core "port" standard later.
- **simai.component-package** — the reproducible build and the receipt are
  general; the rest is Smart-specific. Candidate for a later "release receipt"
  core, not now.
- composite-component, dynamic-composite-component, interface-fragment,
  interaction-rules, effect — interface-specific; stay in the Framework.

## Rollout proposed

1. Owner's review of this draft — done 2026-11-02; Framework thread's second
   review done (ui-control 0a164e3).
2. Transfer and rename the repository to `simai/standards`, then publish the
   core `simai.linkage` 1.1.0 there (`standard-contract`
   envelope, core schemas, a reconcile reference implementation with fixtures for
   all three profiles). The Framework thread checks that its profile is 1.0.0
   unchanged; ui-source then pins the core by digest and keeps its scripts.
3. `mirai-documents` adopts the `norms` and `templates` profiles: template
   passport with content hash and the hash-moves-version gate, registry
   snapshots and compare, the document passport as a usage record, reconcile
   replacing `templateStatus` / `affectedDocuments`.
4. `simai.change-lifecycle` split (its own draft), before or with step 2.

## Open questions for the owner

1. Version: 1.1.0 (additive, Framework unchanged) — recommended — or 2.0.0.
2. ~~Repository name~~ — decided 2026-11-02: this repository moves from
   `zabarov/ai-first` to the `simai` organization as **`simai/standards`**, in
   one step at the release of linkage 1.1.0. The AI First standard keeps its
   name.
