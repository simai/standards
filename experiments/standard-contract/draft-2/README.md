# Standard Contract draft-2

Describe how an object selects standards, how standards inherit requirements or
use other contracts, and where their specification is located. This edition is
an experimental local implementation, not a stable international release.

Read [SPEC.md](SPEC.md) for normative semantics, [PROMPTS.md](PROMPTS.md) for
copy-ready AI instructions, and [federation handoff](FEDERATION-HANDOFF.md) for
integration. Draft-1 remains at its existing entry point, one directory above.

## Run the examples

Use the AI First repository's Python environment (`jsonschema` is already in
`requirements.txt`). Commands below start from the repository root:

```sh
.venv/bin/python experiments/standard-contract/draft-2/contract.py resolve \
  experiments/standard-contract/draft-2/examples/project/project.json docs/api/button.md

.venv/bin/python experiments/standard-contract/draft-2/contract.py resolve \
  experiments/standard-contract/draft-2/examples/project/project.json docs/tutorials/start.md

.venv/bin/python experiments/standard-contract/draft-2/contract.py resolve \
  experiments/standard-contract/draft-2/examples/project/project.json src/components/button.json

.venv/bin/python experiments/standard-contract/draft-2/contract.py standalone \
  experiments/standard-contract/draft-2/examples/portable/button.md.standards.json
```

The first example reports a consistent adjacent declaration and the API profile
with its foundation. The tutorial has another layout profile. The component uses
utility contract bytes but imports no utility requirements. The standalone example
works after copying the entire `portable` directory elsewhere.

`relations` shows where each standard/material came from, why it was included,
its local path, optional original URL and availability. `requirements` retain
source identity, version and digest. `normativeContext` describes only availability
of the inherited standards and directly used contract/specification bytes.

To check structured artifact data:

```sh
.venv/bin/python experiments/standard-contract/draft-2/contract.py resolve \
  experiments/standard-contract/draft-2/examples/project/project.json docs/api/button.md \
  --artifact experiments/standard-contract/draft-2/examples/project/api-projection.json
```

Expected exit 2: language/layout checks pass but editorial obligations require
review. A projection is not proof that the actual Markdown or rendered page has
those properties. Resolution itself always says conformance was not assessed.

## Install in a project

Vendor `contract.py` and the three adjacent schema files together, along with the
specification and the repository license. Use Python 3.10+ and `jsonschema`.
Keep a project configuration at your authorized bundle root and standards inside
it. Choose the project's own stable standard identifiers, exact versions, kinds
and prefixes. Never treat the example rules as approved rules for a real product.

A standard may use sibling paths or relative `..` inside the allowed root. Keep
local copies pinned with SHA-256; URLs are source navigation only. For an arbitrary
contract, write a `uses` reference and describe the public interface or portion
that matters. For inherited requirements, use `extends`. Use `references` for
background reading. Use `specification` to locate the format description, not to
activate a downloaded reader. The example's `format.md` is a byte-identical local
snapshot of this edition's `SPEC.md`, not an independently maintained source.

To prepare an adjacent declaration, preview first:

```sh
python tools/standard-contract/contract.py declare standards.project.json docs/api/button.md
python tools/standard-contract/contract.py declare standards.project.json docs/api/button.md --write
```

These illustrative commands assume the tool was vendored under
`tools/standard-contract`. They create `docs/api/button.md.standards.json` only
with `--write`, never overwriting existing content. The object's directory must
already exist. The file need not repeat inherited parents: it records the directly
selected standards. Existing declarations must be reviewed explicitly when project
bindings change; checking fails if one is stale.

Standalone operation is explicit. Put the object, its adjacent declaration and
all referenced standard/material files beneath the declaration's directory.
Project-level declarations may refer upward within their project root; copying
just that declaration is insufficient to make a portable bundle.

## Version planning update

For new migrations and dependency updates, use the
[explicit lifecycle workflow](../lifecycle/README.md) and its
[federation handoff](../lifecycle/FEDERATION-HANDOFF.md). It requires explicit target
versions. The automatic PATCH migration documented below is retained only as a
historical interface and is not recommended for new adoption.

## Upgrade draft-1

```sh
.venv/bin/python experiments/standard-contract/draft-2/migrate.py \
  experiments/standard-contract/examples/project.json

.venv/bin/python experiments/standard-contract/draft-2/migrate.py \
  experiments/standard-contract/examples/project.json --output /tmp/standard-contract-converted
```

The first command previews; the second creates a new directory that must not exist
and must be outside the source tree. Source files stay unchanged. Only reachable
standards, the project configuration and `migration-report.json` are written;
objects, unrelated content and old generated outputs are not copied.

The report lists proposed patch version increments and all missing locations.
Converted `uses` identities remain unchanged: missing information is never inferred
from matching names in the project. Review and reserve the proposed versions with
the owner before publishing. If a proposed version is already in use, allocate a
fresh owner-approved version and repin the affected dependency chain. These are
local migration outputs, not a release or automatic project activation.

After supplying missing normative links, recalculate dependency pins bottom-up,
regenerate and review adjacent declarations, and run both resolution and applicable
artifact checks. Keep old bindings usable until migration is accepted.

## Checks and boundaries

```sh
.venv/bin/python -m unittest discover -s experiments/standard-contract/draft-2 -p 'test_*.py'
.venv/bin/python -m unittest discover -s experiments/standard-contract -p 'test_*.py'
.venv/bin/python tools/check_candidate02.py
.venv/bin/python tools/check_candidate10.py
.venv/bin/python tools/check_repository.py
```

Exit 0 means operation success, not necessarily artifact conformance. Exit 1 is
an error or failed check; exit 2 means manual assessment or normative context is
outstanding. Read the report type and fields.

No URL fetching, Markdown front-matter interpretation, signatures, automatic
waivers, arbitrary command execution or authoring engine is included. Repeated
resolution is deterministic; identical AI-generated prose/code and generator
idempotence still require separate domain evidence.
