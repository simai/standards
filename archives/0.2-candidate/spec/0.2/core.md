# AI First 0.2 core — candidate 0.2.0-rc.1

Status: local pilot candidate 0.2.0-rc.1; no public release.
This document defines wire version `0.2`. The [0.1 core](../core.md) and its
unversioned schemas remain unchanged. A reader MUST dispatch on `formatVersion`
and MUST NOT interpret a 0.1 catalog using 0.2 revision rules. Unsupported versions
fail closed. MUST, SHOULD and MAY express requirement strength in this draft.

## Purpose and minimum publication

A publication describes a resource, its readable materials and optional
capability contracts. It is neither an agent instruction authority nor permission
to execute an operation. Ordinary sites need only one UTF-8 JSON `ai.json` with
`format`, `formatVersion`, `document`, `revision` and `resource`. Items, catalogs,
capabilities, routing, translations and access hints are optional.

The 0.1 item/resource fields, exact product-version matching, published-state
filter, full representations, scope rules and JSON lexical restrictions apply
unless explicitly replaced below. A format version is not a product version.
Unknown optional fields MUST be ignored; unknown `requires` profiles MUST fail.
Supported profiles in this draft are `core`, `knowledge`, `capability`,
`selective-catalogs`, `translations`, and `protected-reading`.
A document using a profile's semantics MUST list that profile in `requires`.
Core includes pinned catalogs, discovery and bounded transport. The three new
profiles add selectors, translation identities and access hints respectively.

## Independently revised catalogs

A catalog has its own opaque `revision` and the manifest's `resourceId`.
Its revision no longer has to equal the manifest revision. Each catalog link
MUST have `href`, `description`, and at least one of `revision` or `sha256`.
`revision` is the expected child revision; `sha256` is the expected digest of the
retrieved UTF-8 JSON bytes, after HTTP content decoding and before JSON parsing.
If both pins are present, both MUST match. All incoming pins MUST be checked,
including a second link to an already visited catalog. A mismatched pin or
resource identity is an error; it is not permission to use a fresher child.

Catalog cycles are errors. Repeated references to the same URL with consistent
pins are allowed and contribute items once. Distinct retrieved catalogs MUST
NOT define the same item ID. Duplicate IDs invalidate unambiguous selection in
the visited set. A reader MUST NOT claim uniqueness outside the visited set.
Changing one shard updates that shard and its ancestors, not unrelated shards.
Publish immutable children first and atomically replace the entry manifest last.

## Selective reading profile

A link MAY carry `select`, an object containing nonempty arrays of `ids`,
`languages`, `products`, `versions` and/or `kinds`. These are **exhaustive upper
bounds** for all descendants, not hints or rankings. Missing dimensions mean
unknown coverage and MUST NOT be used to skip a link. Values within a dimension
are OR; supplied query dimensions combine with AND. Product IDs, item IDs and
versions compare exactly; language tags compare case-insensitively. A catalog
that promises an empty array is invalid. Keyword queries cannot prune catalogs.

A reader MAY omit a link only when a supplied query dimension is disjoint from
its corresponding declared bound. The parent containing the link MUST require
`selective-catalogs`. The reader MUST verify declared bounds against every
visited descendant; an inconsistent index is `selector-mismatch`. Unvisited
bounds remain publisher assertions, not independently verified facts.

Results MUST include `completeness`: `complete` (whole reachable inventory
visited without errors), `targeted` (some catalogs deliberately omitted and no
visited-catalog error), or `partial` (one or more attempted catalogs failed).
Include `omittedCatalogs` and structured errors. A targeted no-match means no
match under the publisher's index; it is not exhaustive absence proof. A
partial no-match is indeterminate. A successfully selected material MAY be
returned despite errors elsewhere, with completeness and those errors attached.
Callers requiring whole-publication validation MUST request full traversal.

## Translations profile

An item MAY have `translationOf`, an absolute URI identifying a language-neutral
work. All translations have distinct item IDs, their own revision and language,
and the same `translationOf`. This URI is identity, not a URL to fetch.
No equal meaning, revision equivalence or translation quality is implied.
The containing document MUST require `translations`.

The default client language policy is exact match only. An explicitly supplied,
ordered fallback language list MAY select a translation of the same work after
no primary-language match. Report requested and selected languages and whether
fallback occurred. An explicit item ID remains exact and MUST NOT silently
switch to another ID. Product and version constraints MUST still match exactly.
Do not infer language fallback from browser locale or a manifest preference.

## Protected reading profile

An optional manifest `access` object contains `required` (boolean), `description`
and optional `documentation` URI reference. It explains how an existing access
system protects publication reads. The manifest MUST require `protected-reading`.
The object is descriptive and never supplies credentials, tokens, cookies,
client secrets or a permission grant. Access hints cannot override HTTP denial.

Credential providers and trust policies belong to the reader's caller and are
supplied separately. A reader MUST scope credentials to an explicitly authorized
origin and path, isolate caches by principal, and never put credentials in
provenance, errors, manifests or logs. A 401/403 is `access-denied`; clients MUST
NOT retry anonymously to substitute another principal's content. Business
capability authorization remains distinct from access to documentation.

## Related resources and API contracts

Optional manifest `related` entries contain `href`, `relation`, `description`.
They identify associated publications, including other domains. They do not
extend resource scope, allowed origins, credentials or network trust, and MUST
NOT be traversed implicitly during inventory. Child `routes` remain same-origin,
strictly subordinate scopes. External retrieval always needs caller policy.

Capability contracts remain locators into existing descriptions. The OpenAPI
binding accepts 3.0.x, 3.1.x and 3.2.x in JSON (`application/json`) or YAML
(`application/yaml`, `text/yaml`, `application/x-yaml`). `operation` remains a
JSON Pointer to `/paths/{escaped-path}/{method}`. YAML MUST use a safe parser:
reject duplicate keys, custom tags, cyclic/expanding aliases, excessive depth,
non-string mapping keys and multiple documents. JSON lexical limits still apply
to the resulting value. Contract binding validation is not full OpenAPI schema
validation and MUST NOT be reported as such. Readers MUST NOT invoke the HTTP
operation. A contract with no suitable HTTP operation MAY use the existing
`external` binding, with an explicit description of its internal locator.
No new business endpoint is required to satisfy this standard.

## Explicit exclusions

Server-side search, version ranges, signatures, automatic OAuth flows and
business execution are outside 0.2. Limits are caller policy and MUST be reported
when they prevent a complete read. Extension fields cannot disable core checks.

### OpenAPI binding details

OpenAPI 3.2 adds `query` and `additionalOperations`. The locator also accepts
`/paths/{escaped-path}/additionalOperations/{case-sensitive-method}` for 3.2.
Methods with fixed fields cannot be repeated through additionalOperations.
Follow bounded Path Item `$ref` chains using JSON Pointers; check each external
retrieval against ordinary client trust policy. Conflicting local operations
alongside a Path Item reference are an error. Empty operations are legal in
3.1/3.2; 3.0 still requires responses. This does not broaden validation into
schema/reference resolution for operation inputs or outputs.

The reference YAML loader bounds parse events and alias expansion, accepts
bounded acyclic aliases, and rejects merge keys and non-JSON tags/types.
Quote response-code keys. These binding decisions follow the
[OpenAPI 3.0.4 specification](https://spec.openapis.org/oas/v3.0.4.html) and
[OpenAPI 3.2.0 specification](https://spec.openapis.org/oas/v3.2.0.html).
