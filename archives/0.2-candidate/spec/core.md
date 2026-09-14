# Core data model (normative)

## C01 Encoding and compatibility
Documents MUST be JSON objects encoded as UTF-8 without a BOM. Duplicate object
keys, non-finite numbers and unpaired Unicode surrogates MUST be rejected.
JSON follows [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259).
Publishers MUST satisfy the corresponding bundled Draft 2020-12 schema.
Readers MUST check `format` is `ai-first`, `formatVersion` is exactly `0.1`, and
`document` is `manifest` or `catalog` before interpreting domain fields.
Distribution patch releases MUST NOT change valid wire meanings.

Unknown optional fields MUST be ignored, not executed or fetched. Authors SHOULD
namespace private fields with `x-<owner>-`. Such fields MUST NOT change the
meaning of defined fields. Required extra semantics MUST be listed in `requires`.
The profile tokens defined here are `core`, `knowledge` and `capability`.
All readers MUST implement core and knowledge. A reader MUST reject a document
with any unsupported `requires` token. Absence of `requires` means no additional
required profile. A capability-unsupported reader MAY skip capability items and
MUST report that omission. An extension cannot weaken a core requirement.

Unless a field has an explicit default below, absence means not declared, never
universal applicability, trust, permission or unlimited support. `null` is not a
substitute for an absent defined field. Empty optional lists mean no listed
entries. Unknown properties may have any JSON value subject to C01 and limits.

## C02 Manifest
Required fields:

| Field | Meaning |
| --- | --- |
| format, formatVersion, document | Recognition: ai-first, 0.1, manifest |
| revision | Opaque nonempty publication snapshot label |
| resource | Resource identity, meaning, scope and publisher assertion |

Optional fields: `requires`, `items`, `catalogs`, `routes`.
A manifest with no items or catalogs is valid and describes a resource only.
Absence of routes means no child resources declared, not none exist.

Required resource fields: `id` (absolute URI identifier), `name`, `description`,
`language`, `scope`, `publisher.name`. Optional `publisher.url` and `homepage`
are informational links; readers MUST NOT fetch them automatically.
`description` MUST explain purpose and boundaries, not contain client commands.
`language` describes metadata language. Use BCP 47 tags; the schema checks only
lexical shape, not registry membership. Clients MUST NOT infer supported content
languages from this value alone.

`scope` MUST resolve to a directory URL ending in `/`, without query or fragment.
Relative scope and links resolve against the containing document's final retrieval
location using [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986). Local documents
use file URI resolution inside the caller-authorized root. Absolute identifiers
need not be dereferenceable; readers MUST NOT fetch an ID as if it were a link.
Identity is not a location. URI identifiers compare as exact strings; publishers
MUST use a single spelling. Scope is an assertion, not ownership evidence.

`revision` identifies the exported publication snapshot. Every included catalog
MUST carry the same revision and resourceId as its manifest. The publisher MUST
change revision whenever defined metadata or represented bytes change. This
snapshot does not identify the product version; `appliesTo` does that. Labels
are opaque and MUST NOT be numerically or chronologically ordered by readers.

## C03 Items and representations
Required item fields are `id`, `kind`, `title`, `description`, `language`,
`revision`, `status`, `source`, `representations`.
`kind` is knowledge or capability. `revision` labels this item's content revision;
it need not equal the publication revision. `source` is the authoritative source
link asserted by the publisher; source availability and truth are separate checks.
IDs MUST be unique throughout one manifest and its entire catalog closure.
Repeated identical entries are also an error, not an implicit merge.

Status is draft, published, deprecated or withdrawn. Readers MUST select only
published items by default. Deprecated means no longer recommended; withdrawn
means the publisher has revoked use. Readers MUST NOT silently substitute such
items. `replacedBy`, when present, names an item ID, not permission to use it.
Publishers SHOULD preserve a withdrawal entry so readers can learn of revocation.

`appliesTo`, if present, contains absolute product ID and a nonempty unique list
of exact opaque version strings. 0.1 defines no range syntax or wildcard. A
version-restricted query MUST NOT match missing applicability. Product IDs compare
exactly, language tags case-insensitively; no implicit language fallback exists.

Representations is a nonempty list. Each representation requires `href` and a
lowercase MIME essence in `mediaType` (no parameters). Optional `role` is full
(default) or summary, `language` defaults to item language, and `sha256` is exactly
64 lowercase hex characters. A representation language MUST equal item language
case-insensitively in 0.1; translations are separate items with distinct IDs.
There MUST be at least one full representation. Full representations MUST convey
the same substantive knowledge, applicability and examples. Summary is not a
substitute for full content. SHA-256 covers exact retrieved bytes after HTTP
transfer framing, with identity content encoding, before text decoding.
A hash detects byte changes; it is not a publisher signature.

## C04 Catalogs
A catalog requires format, formatVersion, document=catalog, revision, resourceId
and items. Optional catalogs lists child catalogs. A catalog link requires href
and description. It MUST point to an AI First catalog document, not a search
response, arbitrary JSON or a manifest. Catalogs share item semantics with inline
items. Inline and external lists are additive; neither overrides the other.

The declared closure is the complete exported inventory for this snapshot and
reader access context. It need not include everything on the site. 0.1 has no
pagination tokens: split large lists into linked catalogs. Failure to finish the
closure MUST yield partial status, never a complete empty search result.
Cycles MUST be detected and reported. Shared catalog references MAY be read once;
duplicate item IDs remain invalid. Limits are defined in discovery.md.

## C05 Child routes
A route requires scope, href (child manifest location) and description. Its scope
MUST be strictly inside the parent resource scope, on the same origin, and end
in `/`. It MUST NOT have query or fragment. Routes with identical resolved scope
are ambiguous and MUST be rejected. Nested scopes MAY overlap: use the longest
matching path on segment boundaries. The child manifest MUST declare exactly the
routed scope. Child publisher, revision, identity and authorization are independent;
metadata MUST NOT be implicitly inherited. Child catalogs are not parent catalogs.

## C06 URI spelling for scopes
Scopes MUST NOT contain percent-encoded path separators or encoded dot segments.
Publishers MUST use unambiguous directory paths. Readers MUST reject ambiguous
scope spellings rather than using them to select a different child resource.
