# AI instruction templates

Replace bracketed project paths. Provide the 1.0 specification and actual
project tool location to the executor; these prompts do not install the tool.

## Describe a standard

```text
Read Standard Contract 1.0 SPEC.md and the source rules at [source].
Create a new 1.0 standard without changing the source documents. Preserve
all obligations and distinguish mandatory requirements, recommendations and
supporting guidance. Record unresolved ambiguity rather than inventing a rule.
Use extends only for inherited obligations, uses for required external contracts,
and references for background context. Link the format description with
specification. Pin all local normative files; add genuine source URLs when known.
Keep an explicit mapping from source requirements to new requirement identifiers.
Validate the schema and prepare a project binding example. Do not activate it in
existing projects or claim conformance from schema validity alone.
```

## Declare selected rules

```text
Resolve [target] using [project configuration] and the 1.0 contract.py tool.
Preview its adjacent declaration using the declare command. If it is absent,
create it with --write. If one exists, compare it with the project rules and report
any mismatch; do not overwrite it. Verify resolution with the declaration present.
The declaration describes selected standards, not evidence that the object follows
them. Preserve the object bytes.
```

## Check an object

```text
Resolve [target] through [project configuration], including any adjacent declaration.
For an explicitly supplied standalone bundle, use standalone with its declaration.
Report conflicts, inaccessible normative content and each requirement's source.
Assess the actual object with suitable domain checks. Report evidence or unknown
for manual requirements. Do not treat a JSON projection as proof of rendered/code
behavior, and do not turn successful resolution into a conformance claim.
Do not edit the object as part of this inspection.
```

## Upgrade a dependency

```text
Inspect the owner-approved new revision of [standard] and identify all affected
local references and declarations. Preserve the old release and preview the
changed requirements before updating pins. Keep exact versions and raw-byte hashes.
Update children bottom-up, then project bindings and reviewed declarations.
Run 1.0 resolution for each affected target and repeat the domain checks.
Report changed obligations, remaining manual review and evidence. Never substitute
a floating latest version, fetch URLs automatically, or publish a release.
```
