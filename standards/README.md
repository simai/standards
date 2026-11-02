# SIMAI standards

Standards in the [Standard Contract 1.0](../standard-contract/1.0/README.md)
envelope that apply across SIMAI sources: the Framework, legal norm registries,
document template libraries and their consumers.

| Standard | Version | What it settles |
|---|---|---|
| [simai.linkage](simai.linkage/1.1.0/standard.json) | 1.1.0 | What is current, what is out of date and what to change: unit passports, release inventories, change reports, usage records, one reconcile. |
| [simai.change-lifecycle](simai.change-lifecycle/1.1.0/standard.json) | 1.1.0 | How a public name leaves a source without breaking consumers: dated policy, append-only change journal, upgrade from the journal. |

## Profiles

One core, several profiles. A profile fixes the id grammar, the version scheme,
the hash method, the dependency constraint and the impact rule.

- **framework**: exactly `simai.linkage` 1.0.0 and `simai.change-lifecycle`
  1.0.0 (1.0.1 on the Framework side re-pins journal schema 1.2.0). Its files
  (`simai.framework.*`) are read unchanged; the schemas in [pinned](pinned) are
  byte copies from `simai/ui-source`.
- **norms**: a mirror of an official source of law. Dated editions, text hash
  after normalization rule `simai.text/1`, force mandatory or default,
  candidate editions until confirmed, unchecked units shown as unverified.
- **templates**: semver document templates whose clauses are anchors that rely
  on, restate, detail or deviate from norms.

## Formats

[schemas](schemas) holds the core formats, `schema_version` 1:
`simai.unit-passport`, `simai.unit-inventory`, `simai.unit-change-report`,
`simai.usage-record`, `simai.reconcile-report` and `simai.change-journal`.
Passport, inventory, change report and journal also accept the Framework
documents through the pinned schemas.

## Reference implementation

```sh
.venv/bin/python standards/linkage.py validate standards/examples/templates/loan.passport.json
.venv/bin/python standards/linkage.py compare standards/examples/framework/inventory-a.json standards/examples/framework/inventory-b.json
.venv/bin/python standards/linkage.py reconcile standards/examples/framework/usage-record.json standards/examples/framework/inventory-b.json --baseline standards/examples/framework/inventory-a.json
.venv/bin/python standards/linkage.py reconcile standards/examples/documents/usage-record.json standards/examples/templates/inventory.json standards/examples/norms/inventory.json --as-of 2027-04-01
```

[examples](examples) are fixtures, not real data: the amending act named in
`examples/norms` is invented. Tests: `tests/test_standards.py`.

The [proposals](../docs/proposals) record how the two standards were drafted and
reviewed.
