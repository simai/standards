# Conformance and error reporting (normative)

## Q01 Roles and evidence
A conformance claim MUST name AI First 0.1, implementation version, tested roles,
profiles, transport and limits. The roles are publisher, reader and validator.
A publisher satisfies encoding, schema and publication invariants. A reader
satisfies discovery, selection, attribution and boundary requirements. A validator
reports the checked subset and any unperformed checks.

Results MUST distinguish:

- **structure**: encoding, schema, profile compatibility and document invariants;
- **publication**: catalog closure, identity/revision consistency, link availability,
  MIME, digests and supported contract locator checks;
- **runtime conformance**: separately authorized execution evidence.

Each dimension uses pass, fail or not-run. Partial inventories MUST be explicitly
marked partial. Successful structure MUST NOT imply publication or runtime pass.
Publication tooling cannot prove knowledge truth, all private-export exclusions,
semantic equivalence of representations or correctness of publisher assertions.
These require review recorded alongside mechanical results.

## Q02 Errors
Equivalent machine-readable codes MAY be used if their mapping is documented.
Reference codes and required distinctions:

| Code | Meaning |
| --- | --- |
| not-found | File absent, HTTP 404 or 410 |
| access-denied | Local permission failure or HTTP 401/403 |
| unavailable | DNS, connection, TLS, timeout or other server failure |
| unknown-format | Not an AI First document |
| invalid-json | Encoding or JSON grammar violation |
| invalid-structure | Defined schema or local document invariant violation |
| unsupported-version / unsupported-profile | Cannot interpret required semantics |
| media-mismatch / unsupported-encoding | Retrieved representation violates transport declaration |
| unsupported-media / invalid-text | No readable full representation / invalid UTF-8 text |
| invalid-entry / invalid-scope / scope-mismatch | Incorrect discovery input or scope assertion |
| ambiguous-discovery | Competing marked links or equal-scope routes |
| redirect-blocked / access-blocked | Reader policy prevents retrieval |
| revision-mismatch / duplicate-id | Inconsistent publication closure |
| cycle / limit-exceeded | Traversal cannot complete within bounds |
| digest-mismatch | Content differs from declared SHA-256 |
| invalid-contract | Advertised operation locator cannot be verified |
| partial-inventory | Selection would rely on incomplete inventory |
| no-match / ambiguous-selection | No matching item / more than one candidate |

Failure of one optional catalog or representation MAY preserve usable results,
but MUST remain visible. A reader MUST NOT claim exhaustive absence from a partial
inventory. The reference `read` command refuses incomplete or ambiguous selection;
`list` returns partial findings with a nonzero exit status.

## Q03 Test corpus and claims
The executable [test suite](../tests/test_standard.py) and
[portable fixtures](../conformance/fixtures/cases.json) cover both valid and invalid
paths. Their coverage map is in [conformance/README.md](../conformance/README.md).
An implementation passing these tests MUST NOT claim independently certified or
complete runtime conformance. Implementations SHOULD publish their additional
checks and untested requirements. No institutional certification is granted here.
