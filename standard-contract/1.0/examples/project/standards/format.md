# Standard Contract 1.0

Status: maintainer-supported stable specification 1.0.0. Envelope version: `1.0`. Document
identity for links: `standard-contract.spec`, document revision `1.0.0`.
This does not change draft-1 or any frozen AI First specification.

## Core and relationships

A standard retains the required fields `format`, `formatVersion`, `id`, `version`,
`title`, `appliesTo`, `requirements`. The format is `standard-contract` and the
version is `1.0`. Requirement levels, additive inheritance, manual assessment
and JSON property equality retain the meanings described in the
draft-1 specification (`standard-contract/SPEC.md`). Equality uses sorted Python JSON serialization,
including its distinction between integer and floating point representations.
The 1.0 path and relationship rules below supersede draft-1 path rules.

Every reference has an identifier and exact three-part version. Optional fields
are `path`, `url`, `sha256`, `description`. A local path and SHA-256 MUST occur
together. Hashes cover raw bytes. HTTP(S) URLs identify sources; credentials in
URLs are rejected. No network fetch takes place and a URL cannot select a parser
or cause execution. Published identity/version content is immutable.

- `extends`: requires a pinned local standard. All its requirements are inherited.
  It must apply to the object's kind. Requirements cannot be overridden or removed.
- `uses`: requires a description of the used contract or portion. Local content
  must exist and match its digest. URL-only content is `not-fetched`; a reference
  without either location is `missing-location` (useful during migration).
  Neither state proves normative context availability. Usage does not inherit
  requirements and does not cause recursive parsing of an arbitrary contract.
- `references`: informative material. Missing or changed local bytes are reported
  but do not add obligations or block artifact conformance. Unsafe paths still fail.
- `specification`: an optional description of the envelope's authoritative
  specification, using the same reference shape. Available local bytes are checked;
  URL-only or unlocated descriptions leave context incomplete. The known format
  and version, never this link, choose the reader. Omission uses built-in semantics.

References to arbitrary contracts prove only byte identity, not their internal
meaning or that a declared identifier occurs inside them. Inherited standard
identifiers and versions are checked against their envelopes.

## Local addressing and limits

Links in a standard are relative to that standard's directory. Links in project
bindings are relative to the project configuration. Links in declarations are
relative to the declaration's directory. Relative `..` is permitted only while
remaining inside the authorized bundle root after symlink resolution.

Absolute paths, backslashes, colon-containing paths, empty path components and
root escapes fail. Targets and project prefixes additionally reject `.` and `..`.
Targets are logical relative paths and need not already exist. The prototype is
for trusted local inputs: 4 MiB per file, 256 inherited standard identities and
64 inheritance levels; it is not an untrusted multi-tenant validation service.

A project bundle root is the configuration directory. A standalone bundle root
is the declaration directory. Relocation requires copying the whole referenced
bundle. No implicit access to sibling repositories or installed standards exists.
Different versions/digests of one inherited standard fail. The same inherited
identity at different physical locations in one resolution also fails: relative
links may have different meanings there. Repeated paths are deduplicated.

## Project bindings and portable declarations

Project configuration uses `standard-contract-project`, version `1.0`, and
retains draft-1 prefix matching and kind semantics. Matching bindings are additive.

An object's declaration is `<object-name>.standards.json`, with format
`standard-contract-declaration`, version `1.0`, `target` equal to the adjacent
object's basename, `kind`, and pinned local `standards` references. It declares
selected rules, not proven conformance. No timestamp, result or signature is
required and no arbitrary checker is activated.

Project resolution automatically checks a present adjacent declaration. Kinds
and sets of directly selected `(id, version, sha256)` MUST match exactly. Both
routes are independently resolved and their requirements must agree. Addresses
may differ but all declared local dependencies must validate. Neither route wins
silently. An absent declaration is allowed when the project binding exists.

Without a project binding, standalone resolution requires an explicit declaration
argument. The tool never falls back to standalone mode after a project error.
The authorized root then becomes the declaration directory. Markdown front matter
and HTML metadata are not interpreted by this edition.

Declaration preparation resolves the project bindings and reports JSON by default.
Only `--write` creates the adjacent file, exclusively; existing files and symlinks
are not overwritten. The parent directory must exist. This operation does not copy
standards: portability is achieved by including the referenced local bundle.

## Output and claims

Resolution contains direct `selected`, inherited `extends`, `uses`, `references`
and `specification` edges, their locations and availability, and each requirement's
source identity/version/digest. Output is sorted and contains no host-absolute path
or timestamp. All paths in a report are relative to its authorized root.

`normativeContext: available` means inherited standards and the directly declared
normative contract/specification bytes are locally available. It is explicitly
bounded by `contextScope: inherited-standards-and-direct-contract-bytes`. It does
not mean transitive closure of arbitrary external protocols or semantic validation.
An unresolved normative link produces `incomplete`. Informative failures do not.

Resolution always reports `artifactConformance: not-assessed`. Optional checking
of a caller-supplied JSON object produces `fail` on violated mandatory equality,
`needs-review` on manual mandatory obligations or incomplete normative context,
and otherwise `pass`. It never edits the object. A JSON projection alone does not
prove correspondence to code, Markdown, a rendered site or runtime behavior.

CLI exits: 0 successful resolution/preview/creation or passing artifact checks;
1 validation/conflict/input failure or failed artifact; 2 artifact assessment
still requires review. Always inspect the operation/report type.

## Migration and versioning

New migrations MUST use an explicit owner-selected target version for every
changed standard, including descendants whose dependency pins change. Use the
optional lifecycle profile's `migrate1` command for draft-1 input. Format changes
require a new MAJOR subject version. No automatic PATCH proposal is normative.
The older `migrate.py` is retained only as a historical demonstration; it is not
an approved stable migration workflow.

Preview is read-only. Explicit output creates only a new directory, preserving
the active project and historical evidence. Revalidate prepared references and
review unresolved semantic compatibility before adoption. The lifecycle profile
defines source snapshot checks, collision scope and candidate status.

Historical drafts retain their original readers. The 1.0 reader rejects unknown
and draft format tokens. AI First may describe either edition as ordinary material;
no new AI First required field is introduced.
