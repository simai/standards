# AI First

**Describe what a resource is, what it offers, and how to use it — starting with
one `ai.json` file.**

AI First 0.1 is an English-language, MIT-licensed **Pilot Specification** for
machine-readable knowledge and capability descriptions. Use it with a static
website, documentation folder, repository or service. It requires no particular
AI vendor, database, application server or SIMAI product.

- [Start using it](docs/quickstart.md)
- [Read the specification](spec/README.md)
- [Understand the scenarios](docs/scenarios.md)
- [Inspect the examples](examples/README.md)
- [Review conformance evidence](conformance/acceptance.md)

```text
Resource root → ai.json → inline items or catalogs → material or existing contract
```

A small publication needs only a manifest pointing to existing files. Larger
resources may use separate catalogs and child-resource routes. An action description
points to its existing contract; discovering it never authorizes execution.

## Try it

Requires Python 3.11+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/aifirst.py validate examples/minimal
.venv/bin/python tools/aifirst.py read examples/catalog --version 3.0 --language en
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/check_repository.py
```

## What is included

| Path | Contents |
| --- | --- |
| spec/ | Normative core, discovery, safety and conformance |
| profiles/ | Knowledge and capability descriptions |
| schemas/ | JSON Schema Draft 2020-12 contracts |
| examples/ | Minimal, catalog, service and shared-site publications |
| tools/ | Reference reader, validator and repository checks |
| tests/, conformance/ | Executable scenarios, negative cases and evidence |
| docs/, decisions/ | Adoption guides, design rationale and standards comparison |

The repository's own ai.json describes its public specification documents.
Optional graph/ and .simai/ files are repository-development metadata, not part of
the AI First format, publication or reader prerequisites.

## Status and boundaries

Distribution: **0.1.0**. Wire format: **0.1**. Ready for controlled project adoption
within the documented scope; it is not an internationally recognized standard.
Tests and examples are first-party. Independent publisher/client adoption and
live operation execution have not been demonstrated. No universal AI auto-discovery
is promised. See [governance](GOVERNANCE.md) for the route to broader maturity.

The ai.json name is already used for other purposes. Never overwrite an existing
unrelated file; use an explicit alternate manifest link. See
[coexistence](docs/migration.md) and [existing work](docs/standards-landscape.md).

Original prose, schemas and code share the [MIT License](LICENSE.md).
See [contribution guidance](CONTRIBUTING.md) and [changelog](CHANGELOG.md).
