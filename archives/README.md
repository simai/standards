# Immutable historical candidate inputs

`0.2-candidate` and `1.0-candidate` contain every file pinned by the original
candidate locks, with their original relative paths and bytes. Original lock files
also remain at `conformance/0.2/candidate.json` and `conformance/1.0/candidate.json`.
These are integrity snapshots, not standalone sites; historical navigation may
refer to files outside the pinned inventory.

The current candidate checkers use these explicit archive roots by default.
Custom `--lock` inputs still check the current repository root. No fallback to
current files is performed for missing archive inputs. The combined release
inventory separately pins current supported files. Historical prose describes
historical status, not the current release status.
