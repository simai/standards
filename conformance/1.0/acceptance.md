# AI First 1.0 candidate acceptance

Candidate: `1.0.0-rc.1`. Wire version: `1.0`. Status: local candidate prepared
for product pilots; stable promotion is pending.

## Local acceptance requirements

- The candidate lock verifies every pinned file.
- Existing 0.1 and frozen 0.2 handlers retain their meanings and regressions pass.
- Python and JavaScript 1.0 readers agree on the shared fixed corpus.
- Selective reading retrieves one shard from a generated 100,000-item inventory.
- OpenAPI 3.0–3.2 JSON/YAML and MCP snapshot locators are validated without
  business execution.
- HTTPS tests use a trusted ephemeral certificate and cover redirect, compression,
  cache, credential, principal, path, and actor-filtered publication boundaries.
- Migration writes to a new tree, preserves source bytes, recalculates catalog
  pins, and validates the staged result.
- Joint export derives `ai.json` and `llms.txt` navigation from one inventory and
  refuses an existing `llms.txt` collision.
- Cross-domain experiments preserve a zero-field mandatory-core delta and keep
  domain comparison logic outside the generic reader.

## Product evidence

Docara and Larena remain separate product-owned pilots. A prepared handoff is not
a returned result. Product acceptance requires a receipt bound to the exact
candidate lock, complete scenario evidence, reproducible local artifacts, and
manual compatibility review. Missing product evidence does not invalidate local
conformance, but blocks any claim of product-backed stable readiness.

## Promotion boundary

Promoting the candidate to stable `1.0.0`, changing the root distribution,
publishing a release, or contacting external communities is outside this local
candidate preparation. Promotion must record the final acceptance evidence and
create a new immutable stable lock if any pinned file changes.

