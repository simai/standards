# Draft-2 acceptance

Date: 2026-09-14. Verdict: implemented and locally verified experimental edition.

| Accepted requirement | Evidence |
| --- | --- |
| Separate version handling | Separate schemas and reader; old input rejected by draft-2; 18 draft-1 regression tests pass |
| Addressed relationship types | Inheritance, usage without import, informative links, local specification snapshots and explicit availability states |
| Portable declarations | Project/sidecar agreement, independently checked sidecar references, target checks, standalone relocation |
| Preview and exclusive creation | No file on preview, successful creation, existing-file refusal |
| Provenance and honest claims | Edges, source revision/digest, context state, not-assessed resolution, manual-review artifact verdict |
| Source-preserving transition | Validated new tree, bottom-up digests, proposed patch versions, addressless usage report, unchanged source snapshots |
| Boundaries | Root traversal and symlink escape failures, missing normative content failure, nonblocking informative absence/digest mismatch, no socket use |
| Reproducibility | Repeated output and input snapshots; moved project and portable bundle produce the same results |
| Interfaces | Real CLI exit 0 for resolution, 2 for outstanding review and 1 for missing binding |
| Documentation and handoff | Usage guide, four AI prompts and federation handoff linked from repository documentation |

26 draft-2 tests and 18 draft-1 tests pass. The repository documentation/link,
English-source and root inventory check passes. AI First candidate integrity
checks pass for 101 files (0.2) and 63 files (1.0). No existing candidate was
re-frozen to hide a change.

No external standard was downloaded. No product repository or federation runtime
was edited. This does not demonstrate a second independent implementation,
full semantic conflict detection, live product conformance or AI authoring
idempotence. The stable AI First release/pilot task remains separate.

Reproduction commands are in [README.md](README.md). The runtime example format
snapshots are verified byte-for-byte against [SPEC.md](SPEC.md).
