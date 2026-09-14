# AI First 1.0 core data model

## 1. Purpose and minimum publication

An AI First publication lets a compatible client identify a resource, select
relevant material, and locate an existing operation contract. A minimal
publication is one UTF-8 JSON object named `ai.json` with five required fields:
`format`, `formatVersion`, `document`, `revision`, and `resource`.

The default filename is a convention, not a reserved global name. A publisher
MUST NOT overwrite an unrelated existing `ai.json`; it MAY use an explicit
alternate address and the discovery declarations defined by this specification.

## 2. Encoding and compatibility

Documents MUST be JSON objects encoded as UTF-8 without a byte-order mark.
Duplicate keys, non-finite numbers, and unpaired Unicode surrogates MUST be
rejected. Readers MUST verify `format` is `ai-first`, `formatVersion` is exactly
`1.0`, and `document` is `manifest` or `catalog` before interpreting fields.

Unknown optional properties MUST be ignored and MUST NOT be executed or fetched.
Private properties SHOULD use an `x-<owner>-` prefix and MUST NOT change defined
semantics. Required extra semantics MUST be named in `requires`. A reader MUST
reject an unsupported `requires` token. An extension cannot weaken core checks.

Absence means not declared. It never means universal applicability, unlimited
support, trust, availability, or permission. `null` is not a substitute for an
absent defined property.

## 3. Manifest and resource

A manifest requires:

| Field | Meaning |
| --- | --- |
| `format` | Constant `ai-first`. |
| `formatVersion` | Constant `1.0`. |
| `document` | Constant `manifest`. |
| `revision` | Opaque nonempty publication label. |
| `resource` | Resource identity, purpose, scope, language, and publisher assertion. |

`items`, `catalogs`, `routes`, `related`, `access`, and `requires` are optional.
A manifest with no item or catalog is valid and still describes a resource.

A resource requires `id`, `name`, `description`, `language`, `scope`, and
`publisher.name`. `id` is an absolute URI identity and MUST NOT be fetched merely
because it looks like a URL. `homepage` and `publisher.url` are informational and
MUST NOT be fetched automatically. IDs compare as exact strings.

`scope` resolves against the final manifest location and MUST be a directory URL
ending in `/` without query or fragment. It is a publication boundary assertion,
not proof of ownership. Language tags compare case-insensitively; the schema
checks lexical shape and does not claim registry validation.

`revision` is independent from product versions and child catalog revisions.
Readers MUST treat it as opaque and MUST NOT infer ordering or freshness from its
spelling.

## 4. Items and representations

An item requires `id`, `kind`, `title`, `description`, `language`, `revision`,
`status`, `source`, and nonempty `representations`. Kind is `knowledge` or
`capability`. IDs MUST be unique in the visited publication inventory.

Status is `draft`, `published`, `deprecated`, or `withdrawn`. Readers select only
published items by default. `replacedBy`, when present, identifies another item;
it is not permission to substitute it. `source` is the publisher-asserted source
location and is not independently trusted merely because it is listed.

`appliesTo`, when present, requires a product URI and one or more exact opaque
version strings. Version ranges and wildcards are not defined. A constrained
query MUST NOT match missing applicability.

Each representation requires `href` and a lowercase MIME essence in `mediaType`.
Optional `role` is `full` by default or `summary`; `language` defaults to the item
language; `sha256` is 64 lowercase hexadecimal characters. Every item requires a
full representation. All full representations MUST preserve the same substantive
meaning, applicability, restrictions, and examples.

Representation language MUST equal item language case-insensitively. A
translation is a separate item. SHA-256 covers exact decoded representation bytes
before text decoding. It detects byte changes and is not a signature.

## 5. Catalogs and pins

A catalog requires `format`, `formatVersion`, `document=catalog`, `revision`,
`resourceId`, and `items`. It MAY link child catalogs. A catalog link requires
`href`, `description`, and at least one of `revision` or `sha256`.

Catalog revision is independent from the manifest revision. A revision pin MUST
equal the retrieved child revision. A digest pin covers the retrieved UTF-8 JSON
bytes after HTTP content decoding and before JSON parsing. If both pins exist,
both MUST match. Every incoming pin MUST be checked, including links to an already
visited catalog.

Catalog resource identity MUST equal the containing manifest resource ID. Cycles
are errors. Repeated URLs with consistent pins MAY be fetched once and contribute
items once. A duplicate item ID remains an error. Publishers SHOULD write
immutable children first and atomically replace the entry manifest last.

## 6. Selective catalogs and completeness

A catalog link MAY include `select` with nonempty arrays for `ids`, `languages`,
`products`, `versions`, and/or `kinds`. These are exhaustive upper bounds for all
descendants, not rankings. Missing dimensions are unknown and cannot justify
skipping the link. Values inside one dimension are OR; query dimensions combine
with AND. Exact comparison applies except language is case-insensitive.

A reader MAY omit a link only when a supplied query dimension is disjoint from
the declared bound. Visited descendants MUST satisfy every applicable ancestor
bound. An inconsistency is `selector-mismatch`.

Inventory results require `completeness`:

- `complete`: the whole reachable inventory was visited without error;
- `targeted`: some catalogs were deliberately omitted using bounds and no
  visited catalog failed;
- `partial`: at least one attempted catalog failed.

A selected item MAY still be returned with partial status and visible errors.
A targeted no-match is limited by publisher assertions. A partial no-match is
indeterminate. Whole-publication validation requires full traversal.

## 7. Translations

`translationOf` is an absolute URI identifying a language-neutral work. It is
identity, not a location. Translations have distinct item IDs, revisions, and
languages. Equal quality or revision equivalence is not implied.

Default selection requires exact language. An explicitly supplied ordered
fallback list MAY choose another translation of the same work after no primary
match. Explicit item ID selection MUST NOT switch IDs. Product and version
constraints still apply exactly. The result reports requested and selected
language and whether fallback occurred.

## 8. Access and related resources

`access` describes an existing publication access mechanism using `required`,
`description`, and optional `documentation`. It never contains or grants a token,
cookie, secret, credential, or business permission. A denial remains authoritative.

`related` entries require `href`, `relation`, and `description`. They are explicit
navigation to associated material. They do not expand resource scope, origin
allowlists, credential scope, or network trust and MUST NOT be traversed
implicitly. Relation text is descriptive in 1.0 and has no universal installation
or dependency semantics.

## 9. Child routes

A route requires `scope`, `href`, and `description`. Its resolved scope MUST be a
strictly subordinate same-origin directory of the parent scope. Query, fragment,
encoded separators, and encoded dot segments are forbidden. Equal scopes are
ambiguous. For overlapping routes, use the longest segment-boundary match.

The child manifest must declare exactly the routed scope. Identity, publisher,
revision, catalogs, and authorization remain independent; no metadata is inherited.

## 10. Explicit exclusions

Server-side search, version ranges, automatic OAuth, signatures, key discovery,
universal service topology, workflow execution, provider switching, and business
operation execution are outside AI First 1.0. Domain materials may describe such
systems, but clients must use their authoritative contracts and policies.

