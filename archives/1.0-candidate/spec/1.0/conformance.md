# AI First 1.0 conformance

## Claims

A claim MUST name AI First 1.0, implementation version, roles, supported profiles,
transport, and limits. Roles are publisher, reader, and validator. Claims report
these dimensions separately:

- `structure`: encoding, schema, profiles, and local invariants;
- `publication`: visited catalogs, pins, identities, representations, MIME,
  digests, and supported contract locators;
- `runtime`: separately authorized operation evidence.

Each dimension is `pass`, `fail`, or `not-run`. Inventory completeness is
reported separately. Structure pass cannot imply publication or runtime pass.
Publication checks do not prove truth, semantic equivalence, private-data
exclusion, service health, or correctness of publisher assertions.

## Errors

Implementations MAY use equivalent codes when they document the mapping. The
reference distinctions include `not-found`, `access-denied`, `unavailable`,
`unknown-format`, `invalid-json`, `invalid-structure`, `unsupported-version`,
`unsupported-profile`, `media-mismatch`, `unsupported-encoding`,
`unsupported-media`, `invalid-text`, `invalid-entry`, `invalid-scope`,
`scope-mismatch`, `ambiguous-discovery`, `redirect-blocked`, `access-blocked`,
`revision-mismatch`, `resource-mismatch`, `selector-mismatch`, `duplicate-id`,
`cycle`, `limit-exceeded`, `digest-mismatch`, `invalid-contract`,
`partial-inventory`, `no-match`, and `ambiguous-selection`.

An optional branch failure MAY preserve usable selected material but must remain
visible. A reader MUST NOT claim exhaustive absence from a partial inventory.

## Conformance corpus

The bundled schemas, fixtures, Python tests, and shared Python/JavaScript cases
are the reference corpus. Passing them is first-party implementation evidence,
not institutional certification or proof of international recognition. A claim
must list skipped requirements and implementation boundaries.

