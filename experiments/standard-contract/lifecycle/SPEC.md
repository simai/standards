# Standard Contract lifecycle profile

Edition: `lifecycle-draft-1`. Status: local experimental implementation.
This profile adds external lifecycle records above Standard Contract draft-2.
It changes neither the standard envelope nor existing readers.

## Independent identities and version rules

Keep separate the envelope's formatVersion, the standard's id/version, and its
exact resolved dependency set. A new release never updates a project implicitly.
A published `(id, version)` has immutable bytes. Unknown lifecycle status does not
mean active. Only exact numeric three-part versions are accepted in profile records.

PATCH corrects presentation without normative semantic change. MINOR introduces
compatible additions while preserving prior mandatory guarantees. MAJOR changes
format compatibility, removes mandatory guarantees or changes obligations so a
formerly conforming object may no longer conform. Version numbers are declarations,
not proof. The comparison tool establishes a conservative structural lower bound;
uncertain prose may require a higher version after owner review.

Reader compatibility is relative to the source envelope reader. Different envelope
versions report incompatible for that old reader; a separate newer tool may support
both. Object compatibility is assessed separately. New mandatory requirements,
stronger levels, narrower applicability and changed mandatory equality constraints
are incompatible. Normative prose, verification changes and changed normative
references require review. Pure title/guidance changes are compatible. Removal of a
mandatory guarantee requires MAJOR even when it relaxes object acceptance.

Dependency pin changes require review because this comparator does not prove
transitive semantic equivalence. A compatible author statement never changes the
automated result. A comparison is not universal theorem proving over arbitrary text.

## External documents

The five schemas beside this specification define:

- `transition`: exact source/target release pins, declared category, rationale,
  required checks, explicit one-to-one requirement replacement mapping and an
  attributed author assessment. Replacements connect removed IDs to added IDs.
- `plan`: source project digest and explicit changes. Each names its old release
  pin/path and targetVersion. Optional replacement is a local file plus digest.
  Requirement content is not edited by the updater except the requested version
  and rewritten references. No category or target version is chosen automatically.
- `catalog`: the supplied local released identities and hashes. Collisions are
  checked there and against the actually consumed baseline standards. Unpublished
  candidate files merely found on disk are not automatically catalogued releases.
- `journal`: ordered decision records with increasing sequence, exact release,
  status, reason and decision source. Append new decisions rather than rewriting
  a standard. Status changes, including explicitly documented reinstatement, are
  allowed; the latest sequence for that release determines its local status.
- `evidence`: object digest, normative-set digest, checker id/version and results
  for every resolved requirement. Results are pass, fail or not-checked; pass/fail
  must reference local hashed evidence files. Recording a result is not proof that
  its evidence supports the claim or that the claimant has authority.

All profile records reject unknown fields and missing mandatory structure.
Catalogs/journals reject conflicting hashes for one id/version. They provide local
consistency, not signatures, global identity ownership or proof of authenticity.

## Comparison and history

Compare requirements by stable local ID. Report additions, removals, changes and
explicit replacements from a supplied transition. Same identity/version with new
bytes is rejected. A supplied transition must match the compared bytes and actual
version change. Reports retain separate reader and object compatibility, required
review questions and author claims. They are deterministic and timestamp-free.

Transitions form a history by connecting exact release pins. The profile does not
invent predecessors from sorted version numbers or automatically issue releases.

## Impact scope

The root is the supplied project configuration directory. Inspect local JSON
standard envelopes, pinned inheritance and usage edges, project bindings, existing
objects under bound prefixes and their adjacent declarations. Propagate impact
through reverse inheritance/usage links; report their relation kinds separately.
Opaque contracts can have usage consumers without being parsed as standards.

Skip `.git`, `.venv`, `node_modules`, `__pycache__`, `output`, `build`, `dist`,
symlink entries and unreadable/non-JSON JSON files; report skipped paths and
checked prefixes. Referenced mandatory standards still must resolve correctly.
Unbound files, future objects, remote contract internals and external consumers
are explicitly outside object coverage. The tool does not claim a global inventory.
Malformed sidecars and project conflicts fail, rather than producing a partial
success report. This local prototype assumes trusted input and bounded projects;
it is not an untrusted multi-tenant indexing service.

## Candidate preparation

Source references in plans are project-root-relative. Replacement paths are
relative to the plan file and must remain inside the project root. Replacement
standard identifiers and versions must match the explicit target entry. References
inside a replacement are relative to that replacement file.

Prepare the selected standards and their reachable local dependencies. Recalculate
inherited/usage pins bottom-up, then project bindings and existing applicable
sidecars. Any changed child requires its own explicit targetVersion; unused plan
entries, stale pins, conflicting versions or insufficient version category fail.
The source project must already resolve, including any existing declarations.

Preserve original output paths where possible. Copy necessary local material;
if an informative material copy would collide with a rewritten standard, preserve
its pinned bytes under `_lifecycle_materials/<digest>/`. No business objects are
copied or edited. Output declarations describe future selected rules, not successful
migration of those objects. Missing manual/domain checks remain outstanding.

Preview performs staging validation in a temporary directory. Explicit output
creates a new directory outside the source tree, refuses existing paths, validates
project/declaration resolution and rechecks source/control-file snapshots before
installing. It never replaces a running project's configuration. The reference
implementation assumes no concurrent writer to the destination; failure removes
only the directory newly created by this operation.

The output is always a candidate requiring review. Uncertain semantics does not
prevent building a valid candidate, but no command automatically accepts it.
Lifecycle eligibility is a separate view: active is eligible, deprecated warns,
draft/withdrawn/unknown are not eligible for new adoption. Historical pinned
resolution remains available for all statuses. Eligibility alone is not readiness.

## Explicit draft-1 migration

The `migrate1` command uses the same explicit plan and local catalog. Every converted
standard needs a targetVersion. It changes the envelope to draft-2 and paths from
project-relative to file-relative, recalculating pins bottom-up. Because the old
reader cannot process the new envelope, this profile requires a MAJOR target change.
Unlocated draft-1 usage links are preserved and reported as missing information.
Optional content replacements are not accepted by format migration: perform that
change separately so requirements and format evolution remain reviewable.

The historical draft-2 migration script remains unchanged for old workflows but
its automatic PATCH proposal is not the lifecycle profile's supported update path.

## Evidence applicability and lifecycle

The normative fingerprint contains the known envelope version, target kind, exact
resolved requirements and all pinned selected/inherited/used/specification inputs.
Informative references are excluded. Available input addresses are excluded so
relocation alone does not stale evidence; unresolved normative links remain explicit.
The checker identity/version binds its declared behavior. Consumers must version
checker changes honestly; this prototype does not attest its binary or environment.

An evidence record must cover each resolved requirement exactly once. Changed object
bytes, normative fingerprint, checker version, evidence bytes or coverage make it
stale for the current assessment. It remains a historical record. A current intact
record reports its recorded claim and `claimVerified: false`; the tool does not
certify arbitrary evidence semantics. Missing evidence files are input errors.

Journal state is reported separately and does not alter the normative fingerprint.
A later withdrawal can block new adoption while leaving the earlier technical
assessment historically applicable to its exact bytes.

## CLI and limitations

Commands emit JSON. Exit 0 means the requested report/candidate was produced;
it never alone means compatible, current, accepted or conforming. Exit 1 means
invalid input or a blocked operation. Inspect compatibility, applicability,
categorySufficient, lifecycle and candidate status fields.

No network retrieval, floating versions, global registry, signatures, live project
application, public release or automated authoring is implemented. AI First frozen
candidates and Standard Contract draft-1/draft-2 preserve their original meaning.
