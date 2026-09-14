# AI First 1.0 requirement traceability

This matrix maps normative areas to structure, implementations, and executable
evidence. It records the primary locations; tests may cover more than one area.

| Requirement area | Normative prose | Schema | Python | JavaScript | Tests/evidence |
| --- | --- | --- | --- | --- | --- |
| Recognition, encoding, profiles | `spec/1.0/core.md` sections 1–2 | both schemas | `aifirst10_core.py` | `aifirst10.mjs` | `test_10_core.py`, `test_10_interop.py` |
| Resource and scope | core sections 3, 9 | manifest | `aifirst10.py`, core | `aifirst10.mjs` | `test_10_reader.py` |
| Items and representations | core section 4 | both schemas | reader/core | JS reader | core, reader, interop tests |
| Pinned and selective catalogs | core sections 5–6 | both schemas | `Inventory` | JS inventory | 100,000-item test and benchmark |
| Translations | core section 7 | both schemas | Python selection | JS exact-language baseline | core/reader tests; JS limitation declared |
| Protected reading | core section 8; discovery/transport | manifest | transport/reader | JS baseline limitation declared | security and transport tests |
| Discovery | discovery/transport | manifest | `aifirst10.py` | `aifirst10.mjs` | reader/interop/transport tests |
| Redirect, TLS, gzip, limits, cache | discovery/transport | n/a | shared bounded transport | JS baseline transport | existing transport regression plus 1.0 security tests |
| OpenAPI/MCP/external contracts | profiles | both schemas | `aifirst10_contracts.py` | unsupported bindings fail explicitly | `test_10_contracts.py` |
| Migration and joint export | migration guide | generated output revalidated | `aifirst10_publish.py` | n/a | `test_10_publish.py` |
| Domain composition and evidence boundary | scope decision and interoperability guide | no new core schema | synthetic adapter | independent fixture client | development-directions corpus |

The 1.0 transport facade deliberately reuses the pinned transport implementation
whose behavior does not dispatch on wire version. Version-specific discovery,
schemas, profiles, and document interpretation remain separate. Unsupported
JavaScript features are reported as unsupported instead of silently approximated.
