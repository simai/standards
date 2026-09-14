# AI First 0.2.0-rc.1

Local pilot candidate. Wire version `0.2`; existing `0.1` tools and contracts
remain supported. This is not a public release or an internationally recognized
standard. Product pilots have not been accepted.

- [Core contract](../../spec/0.2/core.md)
- [Discovery and transport](../../spec/0.2/discovery-and-transport.md)
- [Publisher, migration and readers](publishing-and-migration.md)
- [Candidate hashes](../../conformance/0.2/candidate.json)
- [Requirement-level acceptance map](../../conformance/0.2/acceptance.md)
- [Verification evidence](../../conformance/0.2/verification.json)
- [Benchmark](../../conformance/0.2/benchmark.json)
- [Docara and Larena handoffs](../../handoffs/0.2/README.md)
- [Discussion package](discussion-package.md)

Check candidate integrity with `python tools/check_candidate02.py`. Contract or
tooling changes after handoff require a new candidate ID, a new immutable lock
file and updated handoffs. Preserve old locks as historical receipts. The user
forwards updated handoff links; this repository task does not message executors.

The unversioned top-level VERSION/README/publication continue to describe the
preserved 0.1 distribution. This directory is the explicit 0.2 candidate entry.
