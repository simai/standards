# simai.linkage 1.1.0 — universal core, draft for the owner's review

Date: 2026-11-02. Status: **draft**, not approved. Nothing here changes a
published standard, a schema or a pin until the owner approves it.

Owner direction of 2026-11-02: the linkage standard becomes universal and its
core lives in ai-first, next to Standard Contract. SIMAI Framework keeps its own
rules as a profile. The first non-Framework users are the norm registry, the
document templates and the client documents of `mirai-documents`.

**Source.** `simai.linkage` 1.0.0, `ui-source/contracts/standards/simai.linkage/1.0.0/standard.json`
(approved 2026-10-27, owner `simai/ui-source`). Every 1.0.0 requirement is kept.
What was Framework-specific (kinds, id grammar, how the hash is taken, the
semver-only version) moves to the Framework profile without change, so every
passport, inventory and change report written under 1.0.0 stays valid.

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
   has a passport: a stable id, a version, its owner and what it is made of.
2. **profile-declared** (must, new). Every passport, inventory and change report
   names its profile and the profile's version. A reader that does not know the
   profile still reads the core fields and says it cannot judge the rest.
3. **id-grammar-by-profile** (must, generalized). An id is `<kind>.<name>` in the
   Framework profile; another profile may use `/` paths (`ru/gk/810`,
   `ru/loan`). Ids are unique within a source; across sources a unit is named
   `<source>:<id>`.
4. **id-never-changes** (must, unchanged). Never reused or silently renamed; a
   rename or renumbering is a new id plus `former_ids` with its journal record.
5. **content-hash** (must, generalized). One SHA-256 over the unit's content.
   The profile names the method: `git-files` (1.0.0: sorted committed files,
   path, zero, length, zero, bytes) or `normalized-text` (text fetched from a
   named source at a recorded time, normalized by the profile's published rule).
6. **version-scheme-by-profile** (must, generalized). `semver` (1.0.0 meaning),
   `dated` (an edition: `since` date and `by` record) or `sequence` (an integer
   that only grows). The scheme decides what "newer" means.
7. **hash-moves-version** (must, unchanged). If the content hash changes, the
   version changes; the release gate refuses otherwise.
8. **dependencies-declared** (must, generalized). A dependency names the unit and
   a constraint in the profile's scheme: a caret range (`^1.2.0`), `in-force`
   (the edition in force on the reference date) or `exact`. Optional fields:
   `from` (the anchor that depends; absent means the whole unit) and `relation`
   (from the profile's list, e.g. `relies`, `restates`, `details`, `deviates`;
   in the Framework `uses`, `reads-foundation`).
9. **anchors-declared** (should, new). A unit that others depend on in part, or
   whose parts depend on different units, lists its anchors with stable ids
   under the same never-reuse rule.
10. **force-declared** (may, new). A unit may state its force for consumers:
    `mandatory`, `default` (consumers may deviate) or `mixed`. Profiles use it in
    their impact rule.

### Time

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

14. **candidate-then-confirmed** (must, new). A version found by an automatic
    check of a source (a changed hash of an official text) enters the inventory
    as `candidate` with what found it; a person or a stated rule confirms it.
    Reconcile reports places affected by a candidate as `unverified`, not
    `action-needed`.
15. **unverified-is-visible** (must, new). A unit whose versions were never
    compared with its source says so (`checked` absent); reconcile shows it, a
    gate may refuse it.

### Inventory and change report

16. **inventory-per-release** (must, unchanged). For the `dated` scheme a release
    is a dated snapshot of the registry.
17. **inventory-is-complete** (must, unchanged).
18. **inventories-compare** (must, unchanged), with anchors: a changed unit lists
    the anchors whose content or dependencies changed.
19. **journal-per-version** (must, unchanged). The entry is data and, for a
    change a consumer acts on, says what to do (`simai.change-lifecycle` record
    form). For a law edition: what changed, quoted from the amending act.

### Consumers and reconcile

20. **consumer-keeps-a-record** (must, generalized). For each place: unit id,
    version, content hash, and optionally the anchor, the relation and the
    reference date it was made on. A document passport of `mirai-documents` is
    a usage record.
21. **record-is-local-data** (must, unchanged).
22. **chains-are-followed** (must, generalizes foundations-count). A consumer may
    itself be a source (templates use norms; contracts use templates).
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
    (`schema_version` 1). The Framework's `simai.framework.*` 1.0.0 formats are
    the Framework profile's formats and are read as the core formats with
    `profile: framework`.
28. **adopt-in-place** (should, unchanged). A norm registry, a template's own
    `template.yaml` and a document passport are extended, not replaced.

## Profiles

| | framework | norms | templates |
|---|---|---|---|
| Owner | simai/ui-source | each jurisdiction of a document library | the document library |
| Kinds | component, utility, plugin, smart, port, tokens, font, icons, module, core | act, norm | template, block, concept |
| Id | `component.radio` | `ru/gk/810` | `ru/loan`, `ru/common/disputes` |
| Version | semver | dated (`since`, `by`) | semver |
| Hash | git-files | normalized-text | git-files |
| Anchors | slots, CSS variables (later) | parts of an article (later) | clauses `[id: …]`, sections `{#…}` |
| Force | — | imperative → mandatory, dispositive → default | — |
| Relations | uses, reads-foundation | — | relies, restates, details, deviates |
| Consumers | Figma kit, docs, products | templates | client documents (document passport) |

The Framework profile is exactly 1.0.0: nothing is added to what a Framework
source must do.

## Related standards that could move to ai-first the same way

Reviewed: the ten Framework standards in `ui-source/contracts/standards`.

- **simai.change-lifecycle** — general in substance (dated two-stage removal,
  append-only journal with machine-applicable records, upgrade from the
  journal). Linkage relies on it for `former_ids` and journal entries, so the
  universal core needs it general as well. Framework runtime notes
  (`SF.deprecations.list()`) and alias tables stay in its Framework profile.
  Must be reconciled with Standard Contract lifecycle, which covers the
  standards' own versions.
- **simai.ai-development** — largely general (contracts before code, generated
  output is not source, exact pins, evidence over report, one writer per
  repository, owner decisions asked, content is data, no secrets, small
  reversible steps). Browser measurement, public CSS variables and English-only
  Framework text stay in the profile. Overlaps with Federation rules: one of the
  two must reference the other, not repeat it.
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

1. Owner's review of this draft.
2. Publish the core `simai.linkage` 1.1.0 in ai-first (`standard-contract`
   envelope, core schemas, a reconcile reference implementation with fixtures for
   all three profiles). The Framework thread checks that its profile is 1.0.0
   unchanged; ui-source then pins the core by digest and keeps its scripts.
3. `mirai-documents` adopts the `norms` and `templates` profiles: template
   passport with content hash and the hash-moves-version gate, registry
   snapshots and compare, the document passport as a usage record, reconcile
   replacing `templateStatus` / `affectedDocuments`.
4. `simai.change-lifecycle` core, then `simai.ai-development` core, each as its
   own draft.

## Open questions for the owner

1. Version: 1.1.0 (additive, Framework unchanged) — recommended — or 2.0.0.
2. Whether the repository is renamed now that it holds several standards (see
   the analysis given to the owner on 2026-11-02).
