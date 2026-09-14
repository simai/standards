# Reproducible publications

| Directory | Scenario | Reader input |
| --- | --- | --- |
| minimal/ | One manifest and one existing Markdown guide | Directory or HTTP root |
| catalog/ | Two versions in an external inventory | Directory, HTTP root or marked page |
| service/ | Existing OpenAPI operation description | Directory or HTTP root |
| collection/ | Parent routes to an independent child | HTTP child page using origin-root discovery |

All example identities and products are fictional. example.invalid is intentionally
non-operational. The service example verifies a contract locator, not a live action.
To test root routing, serve collection/ as the server document root. When serving
catalog/, its index.html marks its own manifest explicitly.

Examples use relative links and work in local copies. The reference CLI defaults
to directory/root input; pass --mode manifest for a direct ai.json path. The
conformance suite supplies an ephemeral HTTP server with deterministic MIME types.
