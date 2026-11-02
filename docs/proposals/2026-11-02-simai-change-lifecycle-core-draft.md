# simai.change-lifecycle 1.1.0 — universal core, draft for the owner's review

Date: 2026-11-02. Status: **draft**, not approved. Companion of
`2026-11-02-simai-linkage-universal-draft.md`: linkage core requirement 19 points
at the journal record form, so the universal linkage core cannot depend on a
Framework standard. The Framework thread's review of the linkage draft
(ui-control `control/evidence/2026-11-02-simai-linkage-universal-draft-review.md`)
asked for this split before or with linkage 1.1.0.

**Source.** `simai.change-lifecycle` 1.0.0,
`ui-source/contracts/standards/simai.change-lifecycle/1.0.0/standard.json`
(owner `simai/ui-source`), with the pinned `change-journal-1.0.0.schema.json`
and `lifecycle-policy-1.0.0.json`. All 16 requirements are kept. What is
Framework-specific moves to the Framework profile word for word; no Framework
file has to change.

## What is general and what is not

General — how any source lets a public name go without breaking its consumers:
dated stages, a published policy, an append-only machine-readable journal,
records that say what to write instead, upgrade from the journal, consumers
told before the removal.

Framework only — the calendar (30-day compat, sweep on day 1, 30-day
extension), the interface kinds and rewrites (`attribute` … `behaviour`,
`rename-attribute` … `replace-component`), `SF.deprecations.list()`, the alias
tables, `scripts/sf-upgrade.mjs`, the browser check.

Not the same thing as the Standard Contract lifecycle profile: that one records
the status of a **standard's release** (draft, active, deprecated, withdrawn).
This one records **public names leaving a unit**. A standard is also a unit, so
both may apply to it; neither replaces the other.

## Core requirements

1. **dated-policy** (must; generalizes one-version-line). A source publishes a
   lifecycle policy: how long a leaving name keeps working and how its removal
   date is computed. A name leaves on a date the policy gives, never undated.
   Profile: the Framework keeps one long version line and a calendar; a
   `semver` source may bind removal to its next major; a mirror source copies
   the dates of the original source.
2. **two-stages** (must, unchanged). Compat: it still works, through an alias or
   a shim, and its replacement is documented. Removed: it is gone. There is no
   third, undated state.
3. **journal-records-every-change** (must, unchanged). Every change that asks a
   consumer to change anything is a record in a machine-readable journal. A
   change without a record is not released.
4. **record-says-what-to-write** (must, generalized). A record names each old
   form and what to write instead, the kind of change (from the profile's
   list), whether the rewrite is mechanical (from the profile's rewrite list,
   or `manual`, or `none`) and, when it is not, an instruction and a
   before/after example a person or an AI can apply.
5. **record-dated-by-policy** (must, generalized). A record carries the date it
   was deprecated and the date it is removed on, computed by the policy.
6. **journal-append-only** (must, unchanged). A record is never deleted; a
   removed name stays as a tombstone.
7. **journal-chronological** (must, unchanged).
8. **no-compat-without-record** (must; generalizes no-alias-without-record).
   Every compatibility the source keeps has a record; one found without a
   record fails the gate.
9. **remove-on-date** (must; generalizes sweep-on-schedule). On or after its
   removal date a compat record is removed from the source and marked removed;
   a compat record past its date fails the gate.
10. **extension-once-with-reason** (must, unchanged; the policy gives the limit).
11. **compat-out-of-the-way** (should, unchanged).
12. **use-is-observable** (should; generalizes runtime-notes-use). A consumer can
    find out that it still uses a compat name without reading the journal by
    hand: a runtime note, a build warning, a reconcile status.
13. **upgrade-from-the-journal** (must, unchanged). An upgrade reads the journal:
    a tool finds every old form, rewrites the mechanical ones and lists the rest
    with their instruction.
14. **consumers-scanned-before-removal** (must, generalized). Before a removal the
    known consumers are scanned and migrated. Under `simai.linkage` the known
    consumers are those whose usage records name the unit; their reconcile
    report shows `former-name` with the removal date.
15. **documented-for-readers** (must, unchanged).
16. **verified-by-gate** (must, generalized). The gate holds the journal's form,
    the policy's dates, the append-only rule and the compat coverage; the
    profile adds its own checks.

### Sources the publisher does not control

M. **mirror-journal** (must for a mirror source, new). A mirror (see
   `simai.linkage` A) records the original source's changes in its own journal
   with the original dates and act (`by`); requirements 8–10 do not apply to
   it, because it neither keeps the compat nor decides the dates. For a repealed
   norm the record says what the consumer does instead.

## Format

One core format `simai.change-journal`, `schema_version` 1: `records[]` with
`id`, `recorded_on`, `stage`, `kind`, `summary`, `items[{from, to, match}]`,
`deprecated_on`, `remove_after`, `extended_to`, `extension_reason`,
`removed_on`, `rewrite`, `examples`, `manual`, `owner`, `source`, plus
`profile` (or implied by a profile-specific schema id). The `kind` and
`rewrite` lists come from the profile. The Framework's
`simai.change-journal.v1` file is read as the core format with
`profile: framework`, unchanged.

## Profiles

| | framework | norms (mirror) | templates |
|---|---|---|---|
| Policy | one version line; compat 30 days; removal on the first sweep day (day 1) on or after deprecation + 30; one extension up to 30 days | the original source's dates (`effective_from`, `effective_to`) | removal at the next major of the template; compat answers kept until then |
| Kinds | attribute, value, event, class, token, utility, option, property, component, behaviour | norm, act | template, parameter, option, field, clause, party |
| Rewrites | rename-attribute … replace-component, manual, none | manual, none | rename-parameter, rename-option, rename-field, replace-template, manual, none |
| Observable use | `SF.deprecations.list()`, opt-in console warning | reconcile `former-name` / `action-needed` | form warns on an old answer; reconcile `former-name` |
| Upgrade tool | `scripts/sf-upgrade.mjs` | — (a person applies the instruction) | answer-set migration (saved answers of clients rewritten mechanically) |
| Gate | `tests/change-lifecycle.contract.test.mjs`, browser check | registry lint | library lint |

The templates profile gives one thing the document builder lacks today: when a
parameter, option or field of a template is renamed, the clients' saved answers
and document passports are migrated by the journal instead of breaking.

## Noted on the way (Framework, not changed here)

- `contracts/changes/journal.json` declares `schema: "simai.change-journal"`
  while the pinned 1.0.0 schema expects `simai.change-journal.v1`; records use
  kinds `global` (2) and `format` (1) that the pinned enum does not list. Either
  the Framework profile lists them or the file follows the pin — the Framework
  thread's decision.

## Rollout proposed

1. Owner's review; the Framework thread checks that its profile is 1.0.0
   unchanged.
2. Publish the core with `simai.linkage` 1.1.0 in `simai/standards`; ui-source
   pins the core and keeps its policy, tools and tests.
3. `mirai-documents`: journals for the library (templates profile) and the norm
   registry (mirror), and the answer-set migration.
