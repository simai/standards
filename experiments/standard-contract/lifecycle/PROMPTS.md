# Lifecycle instructions for AI executors

## Compare revisions

```text
Read Standard Contract lifecycle SPEC.md. Compare [old standard] and [new standard]
using lifecycle.py compare. Identify changed requirement IDs, dependencies and
reader/object compatibility separately. Prepare an external transition record with
exact pins, rationale, checks and explicit replacements where justified. Keep the
author's assessment separate from automated findings. Do not infer unchanged
normative meaning from similar wording or choose a version automatically.
```

## Assess impact

```text
Run lifecycle.py impact for [standard ID] in [project configuration]. Explain
which standards, bindings, existing objects and sidecars are affected through
inheritance or usage. Report checked prefixes, exclusions and unknown external
consumers. Keep existing pins and objects unchanged. A later release being available
does not authorize updating the project.
```

## Prepare an update

```text
Use [owner-approved explicit version plan] and [local release catalog] to prepare
an update of [project configuration]. Preview with lifecycle.py prepare. Report
missing child versions, collisions, stale pins and unresolved compatibility.
If structurally valid, write to [new absent directory] only. Validate the generated
configuration and declarations. Do not copy or transform business objects, activate
bindings, publish releases or claim that a candidate has been accepted.
```

## Review the new bundle

```text
Resolve the prepared bundle with the draft-2 reader. Review comparison and lifecycle
reports separately. Check whether existing receipts apply to the exact object bytes,
normative set and expected checker version using lifecycle.py evidence-check.
Preserve stale receipts as historical evidence. Run needed domain checks and record
new evidence explicitly; matching hashes do not prove a review's semantic correctness.
List outstanding manual checks and excluded consumers before owner acceptance.
```
