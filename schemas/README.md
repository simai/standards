# JSON Schema contracts

manifest.schema.json and catalog.schema.json use JSON Schema Draft 2020-12.
Their local `$defs` are identical and self-contained; validation does not fetch a
remote schema. No hosted `$id` or schema URL is claimed by this initial distribution.

Use the reference validator or any Draft 2020-12 implementation. Schema validation
checks types, required fields, literals and lexical constraints. Normative prose
also requires duplicate-key rejection, supported required profiles, full
representations, scope semantics, catalog consistency and safe traversal. A schema
PASS alone is therefore not full AI First conformance.

Unknown optional fields are intentionally allowed. Publishers should use x-owner-
prefixed extensions; required additional meaning must be declared through requires.
URI and language patterns check lexical shape, not registry ownership or membership.
