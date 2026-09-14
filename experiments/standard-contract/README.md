# Standard Contract

A usable local experiment for giving different standards one envelope, explicit
composition and reviewable requirements. Start with the examples, then read the
[specification](SPEC.md). This is draft 1, not a released international standard.

## Try it

From the AI First repository root, using Python 3.10+ and the existing
`jsonschema` dependency (`requirements.txt`):

```sh
.venv/bin/python experiments/standard-contract/resolve.py \
  experiments/standard-contract/examples/project.json docs/api/button.json

.venv/bin/python experiments/standard-contract/resolve.py \
  experiments/standard-contract/examples/project.json docs/tutorials/start.md

.venv/bin/python experiments/standard-contract/resolve.py \
  experiments/standard-contract/examples/project.json src/components/button.json
```

The API page receives `docs.foundation` and `docs.api`. The tutorial receives
`docs.foundation` and `docs.tutorial`. The component receives its own obligations;
its `uses` relationship does not import utility implementation rules.

Check a structured page description:

```sh
.venv/bin/python experiments/standard-contract/resolve.py \
  experiments/standard-contract/examples/project.json docs/api/button.json \
  --artifact experiments/standard-contract/examples/api-page.json
```

Expected: language and layout pass; links and parameter completeness require
review. Exit code 2 is intentional. Change the layout to `tutorial` and the API
page fails. This JSON file is a teaching fixture, not proof of a built Docara page.

## Adopt in a project

1. Vendor `resolve.py`, `standard.schema.json` and `project.schema.json` together
   into a tools directory, preserving this draft's specification and license.
   Install `jsonschema` in the project's Python environment.
2. Start with existing rules. Write one standard JSON per coherent concern.
   Keep requirement identifiers stable; distinguish mandatory text from advice.
   Use `manual` for arbitrary content rather than inventing an unverified check.
3. Place a configuration file, for example `standards.project.json`, at the
   project root. Store the referenced standards under a project-local directory.
   Copy the example bindings and adjust prefixes and object kinds to the project.
4. Pin each standard's exact version and SHA-256. On macOS/Linux, inspect a file
   digest with `shasum -a 256 path/to/standard.json`. References, including parent
   references, are relative to the project configuration directory. When updating
   a parent, update and repin its descendants from parents toward leaves, then
   update the project binding. Do not resolve to a floating `latest`.
5. Before asking an AI to create or edit a file, run the resolver for that target.
   Supply the resulting requirements and the actual object to the AI.
6. Review the diff against the requirements. Run relevant domain checks and
   record evidence for manual items. Preserve compliant content. Repeat a real
   authoring run to measure whether it makes no further changes; the resolver
   alone cannot certify generator idempotence.

The examples are illustrative standards, not authoritative new rules for the
framework, Larena or Docara. Their product owners must approve actual adoption.
No product repository was changed by this experiment.

For Docara, start with two explicit sections: API reference and tutorials.
For a framework, start with utility and component object kinds. Later add smart
components, pages and product-specific profiles only where real rules differ.
A product using a component consumes its public contract; it should not import
all internal coding requirements transitively.

## Instruction to give an AI

```text
Resolve the target file against standards.project.json using the project resolver.
Read all resulting mandatory requirements and identify outstanding manual checks.
If resolution fails or requirements contradict each other, report the conflict.
Make the smallest changes needed for the requested task and applicable rules.
Preserve content that already conforms. Do not invent exceptions or upgrade pins.
Report each relevant requirement as satisfied with evidence, violated, or unknown.
Do not claim artifact conformance from successful resolution alone.
```

## Adding a standard

Use [docs.api.json](examples/standards/docs.api.json) as a child-standard template
or [framework.utility.json](examples/standards/framework.utility.json) for a
self-contained standard. See [project.json](examples/project.json) for binding.

A manual requirement can contain detailed Markdown, code examples or a table in
its `text`. `guidance` is optional explanatory text. Unknown mandatory semantics
are rejected. Do not hide required behavior in the optional `extensions` object.

## Verification and limitations

```sh
.venv/bin/python -m unittest discover \
  -s experiments/standard-contract -p 'test_*.py'
```

The test corpus covers inherited and separate section rules, non-inheriting
usage, repeatability without source writes, duplicate binding deduplication,
changed digests, identity conflicts, conflicting property values, applicability,
missing bindings, path traversal, symlink escape, duplicate JSON keys, unknown
verification methods, and honest manual-review reporting.

The prototype does not execute rules, edit artifacts, fetch remote standards,
certify arbitrary prose conflicts or prove that different AI models generate the
same result. Existing documents require editorial decomposition into requirements;
renaming a document or converting it to JSON does not remove ambiguity.

See [CHANGELOG.md](CHANGELOG.md) for this experiment's revision history and the
repository [license](../../LICENSE) for reuse terms.
