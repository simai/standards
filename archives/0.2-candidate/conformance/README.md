# Conformance kit

Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

The suite creates an ephemeral loopback-only server and closes it afterward.
No model, product server, credential or external API is needed. A sandbox may need
to permit binding 127.0.0.1 for the HTTP cases. Do not replace them with mocked
page-load claims. Tests modify only temporary copies of examples.

## Requirement coverage
| Requirements | Evidence |
| --- | --- |
| C01 | schema validity, fixture matrix, duplicate keys, BOM, NaN, Unicode and nesting |
| C02/C03 | minimal manifest, exact bytes and attribution, statuses, version/language/product filters |
| C04 | external catalog, revision mismatch, cycle, duplicate ID, partial inventory |
| C05/D01 | marked page, root fallback and child routing, duplicate routes, scope mismatch |
| D02/K01 | raw text, digest change, fallback, missing source, MIME and unsupported media |
| D03/S03 | all budget dimensions, local escape, symlink, remote-to-file, origin and IP policy |
| D04 | snapshot mismatch, offline flag; persistent cache is absent |
| A01–A04 | OpenAPI locator, bad pointer, MCP snapshot, GET-only capability discovery |
| S01 | malicious instruction returned as data; no resulting file write |
| Q01/Q02 | separate result dimensions, CLI partial/no-match/ambiguity exit status |

Human review is still required for C03 full-representation equivalence, K02 prose
applicability, A01 side effects and S02 private export exclusion. Reference checks
do not prove arbitrary LLM resistance to prompt injection or a live API's safety.

## Portable cases
`fixtures/cases.json` maps each JSON file to its expected structure outcome.
`valid.json` is a structure fixture, not a standalone publication: its material
is intentionally supplied by scenario tests. Publication failures use temporary
mutations of examples, with readable expectations in the suite.

## Implementation report template
Record implementation and version, date, OS/runtime, wire version, roles,
profiles, transport, test command, pass/fail counts, limits, source digests,
manual-review findings and untested behavior. Distinguish first-party from
independently authored implementations. See acceptance.md for this delivery.
