# Publisher guide

## Ownership and minimal work
Keep the existing source of truth: Markdown, a typed record or an existing API
contract. Publish metadata pointing to it. For a few pages, edit ai.json directly;
for generated documentation, generate the manifest and catalogs from the same
content inventory. Do not scrape rendered HTML into a second authoritative model.

Every item needs purpose, language, status, revision, source and representations.
Scope is relative `./` for portable packages. Version applicability uses exact
strings; do not write `>=3`, `latest` or `*` intending range matching. A version
named `latest` is just that exact opaque string in 0.1.

## Deterministic publication procedure
1. Inventory only material intended for this audience. Explicitly exclude private
   pages, credentials, unpublished drafts and internal paths.
2. Assign stable resource and item IDs. Changing URLs need not change identity.
3. Generate full representations and raw examples from the authoritative model.
4. Calculate optional SHA-256 over final bytes, after line-ending decisions.
5. Set new item revisions for changed content and one publication revision on
   manifest and all catalogs. Metadata-only publication changes also change it.
6. Run structure and publication checks against a staging directory.
7. Review semantic equivalence, applicability, source ownership and access.
8. Publish the complete snapshot and switch the entry manifest last or atomically.
9. Verify through HTTP using the same reader path a consumer will take.

Do not publish the entire standard repository as a document root; it includes
implementation files and local development directories. Export only your intended
publication. Relative references make copying the approved subset straightforward.

## Updates, removal and translations
Retain deprecated or withdrawn entries where feasible; name replacement IDs.
Never silently reuse an old ID for a different concept. Update hashes whenever
bytes change, including line endings. A hash failure after deployment usually
means mixed or stale files, not a reason to disable verification.

Translations have separate IDs/revisions. Record their real applicability and
language. A translated summary must not masquerade as a full representation.
Metadata can be localized through separately published inventories in 0.1; clients
must not infer automatic fallback or cross-locale synchronization.

## Shared hosting
If you own a subdirectory, publish its ai.json there and add marked alternate
links to its HTML pages. If you control the origin root, its manifest can route to
child products. Paths are matched on directory boundaries, with longest match.
A child description is self-contained; publisher and access do not inherit.

## Product integration without coupling
A Docara, CMS or other generator needs only an export step over its own public
content model, output files and CI validation. This repository does not modify
any product. A concrete integration should record generator version, source
revision, exported path list, validation report and the actual consumer outcome.

## Reference exporter example
This repository uses `python3 tools/build_manifest.py` to generate its own ai.json
from ten explicitly listed public documents. Item revisions are content hashes;
the publication revision derives from the complete item inventory. Running it
twice without source changes produces the same bytes. `--check` detects a stale
export without changing files. A product adapter should follow the same pattern
with its own existing content inventory, rather than recursively exposing files.
