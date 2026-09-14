# Standard Contract: draft 1

Status: experimental specification, implemented locally. This is a separate
contract for describing and composing standards, not an amendment to the frozen
AI First 1.0 candidate. The name is provisional. No international adoption or
cross-model semantic equivalence is claimed.

## Purpose and conformance

A standard may describe code, prose, visuals, data or any other subject. Its
machine-readable envelope identifies its requirements and application scope.
A conforming publisher satisfies the standard schema and the semantic rules
below. A conforming resolver satisfies the project schema and resolution rules.
Artifact conformance is a third, separate claim: successful resolution alone
does not prove that code, prose or a product follows the requirements.

The terms MUST, MUST NOT, SHOULD and MAY express obligations, prohibitions,
recommendations and permissions in this draft. They do not grant authority to
execute actions. A project owner explicitly opts into a set of standards.

## Standard envelope

[standard.schema.json](standard.schema.json) defines the envelope. Required
fields are `format`, `formatVersion`, `id`, `version`, `title`, `appliesTo`,
and `requirements`. Optional fields are `extends`, `uses` and `extensions`.

- `format` is `standard-contract`; `formatVersion` is `draft-1`.
- `id` is an owner-assigned stable identifier. Publishers SHOULD use a namespace
  they control, for example `org.example.docs.api`. There is no central registry.
- `version` is an exact three-part version of this particular standard. It is
  independent of the envelope version. Published `(id, version)` content MUST
  be immutable. Correcting content requires a new version and explicit repinning.
- `appliesTo` lists project-agreed object kinds, such as `component` or `api-page`.
  Kind names are exact, case-sensitive tokens, not a universal taxonomy.
- Each requirement has a locally unique `id`, normative `text`, a `level`
  (`must`, `should`, `may`) and a `verification` method.
- Optional `guidance` provides non-normative explanation and examples.
  Requirements MUST NOT depend on normative rules hidden only in guidance.
- `extensions` contains optional owner-defined metadata. A consumer may ignore
  it. Mandatory behavior MUST NOT be hidden in extensions.

The normative `text` can contain arbitrary Markdown, including tables and code.
Images, long documents and other external material may be mentioned, but this
resolver does not retrieve, pin or evaluate them. If their content is necessary
for an assessment, the reviewer must record the exact reviewed revision and
cannot report success when the material is unavailable. In the initial draft,
keep self-contained obligations in `text` and use external material as supporting
context. A pinned external-content binding is future work.

## Composition

`extends` contains exact references: `id`, `version`, `path`, `sha256`.
The SHA-256 covers raw file bytes. Every reference path, including a transitive
one, is relative to the directory containing the project configuration.

Extending a standard adds all of its requirements. A child MUST NOT silently
weaken, replace or delete a parent requirement. The inherited standard MUST
also apply to the selected target kind. Diamond inheritance is deduplicated.
A cycle, unknown version, missing file or changed digest is an error. Different
versions or digests for the same standard identifier in one resolution are errors.

`uses` records an exact external contract identity and a description of the
relationship. It does not import requirements, prove installation or verify the
referenced contract. Any mandatory usage obligation must appear as a requirement
of the consuming standard. A component using a utility does not inherit utility
implementation rules merely because of this relationship.

There is no implicit priority, last-writer-wins rule or path-specific override.
All matching bindings contribute requirements. To relax a rule, publish a revised
standard or choose a different explicitly agreed profile. Automated waivers and
conditional-rule expressions are deferred; never silently skip a requirement.

## Project binding and resolution

[project.schema.json](project.schema.json) defines a `standard-contract-project`
with `formatVersion: draft-1` and one or more `bindings`. Each binding declares:

- `prefix`: a normalized project-relative POSIX path;
- `kind`: the target object kind;
- `standards`: one or more exact pinned references.

A prefix matches the exact target or descendants separated by `/`. It is not a
shell glob: `docs/api` does not match `docs/apix`. Paths MUST NOT be absolute or
contain backslashes, empty components, `.` or `..`. Matching is case-sensitive.
Target paths are logical identifiers; the resolver need not open the target file.
If no binding matches, resolution fails rather than claiming no obligations.
If overlapping bindings declare different kinds, resolution fails.

References are local files confined to the project configuration directory after
symlink resolution. No network fetch, package installation or recorded command
execution occurs. The implementation limits transitive depth to 64 and loaded
standard identities to 256. A hostile publication still requires a sandbox and
caller-controlled resource budgets; this local prototype is for trusted project
inputs and is not a hardened untrusted-input service.

The resolver returns all selected standard identities and digests, with the full
requirements sorted by `standard-id#requirement-id`. No timestamp or host path is
included. A consumer MUST NOT ignore an unknown envelope version, unknown
verification method or unrecognized mandatory field.

## Verification

`manual` means a human or a separately evaluated domain checker must assess the
normative text. The reference checker always reports `needs-review` for it.
A language model's confident assertion is not automatic evidence.

`equals` is a deliberately small optional verification mechanism for a top-level
property of a JSON object. The requirement must have level `must`, name the
`property` and provide `value`. Missing is different from present null. JSON
booleans are different from numbers. Object-key ordering is ignored; arrays are
ordered. In this implementation comparison uses sorted Python JSON serialization:
`1` and `1.0` are distinct. This serialization detail must be matched by future
implementations or revised explicitly; no cross-language equivalence is claimed.
The normative text MUST agree with the machine constraint.

Two unequal mandatory values for the same property produce a resolution error.
This detects only conflicts expressible by this mechanism. Contradictions in
arbitrary prose MUST be reviewed; their absence is never proved by schema checks.
There is no universal conflict solver.

The artifact checker reports `fail` when any mandatory machine check fails,
`needs-review` when mandatory manual obligations remain, otherwise `pass`.
Recommendations and permissions remain visible but do not block conformance.
A `pass` covers only the declared obligations in the supplied object and is not
proof of correspondence to a separately built page, source code or live system.
Domain adapters must establish that correspondence using actual product sources.

CLI exit codes: 0 = resolution succeeded or artifact checks passed; 1 = invalid
input, resolution failure or failed artifact; 2 = artifact review outstanding.
Check the report type and operation before interpreting exit code 0.

## Repeatability and idempotence

With fixed inputs, pinned dependencies and the same resolver implementation,
resolution MUST return the same ordered result regardless of binding order.
Repeated resolution MUST NOT modify sources. The reference checker also reads
artifacts without modifying them.

An authoring tool using the contract SHOULD preserve already conforming objects
and repair specific violations. A generator claiming idempotence must separately
prove `apply(apply(object)) = apply(object)` for its advertised domain, including
user edits and manual requirements. This draft does not implement such a generator
and does not promise identical prose or code from different AI models.

## AI First relationship

AI First may publish this specification or an individual standard as ordinary
knowledge material and link its authoritative contract. Finding a standard does
not activate it: project bindings determine applicability. This draft adds no
mandatory AI First fields, profile tokens or resolver behavior.

## Future decisions

Evaluate real standards before adding conditional predicates, exceptions, domain
checker bindings, external content digests, remote distribution, signatures or
cross-language normalization. A future stable envelope can be called `1.0` once
its semantics and implementations are accepted. Standards described by the draft
may themselves use version `1.0.0`; the two version axes must not be confused.
