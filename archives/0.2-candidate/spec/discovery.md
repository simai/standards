# Discovery and reading (normative)

## D01 Entry selection
A caller MUST distinguish a direct manifest, a resource root and a web page.
No content-guessing is needed for a direct manifest; the final filename may vary.
A local directory root appends `ai.json`; readers MUST NOT search its parents.
An explicitly supplied HTTPS resource root ending in `/` appends `ai.json`.
For a page URL, readers implementing page discovery MUST:

1. Fetch the page under their network policy, retaining its final URL.
2. Inspect HTML `link` elements with rel token `alternate`, type `application/json`
   and `data-ai-first="0.1"`. Resolve href against final page URL. This profile
   intentionally does not use HTML base elements. Publishers MUST provide at most
   one distinct marked target. Multiple targets are discovery ambiguity.
3. Use that target if present; if invalid or inaccessible report its error without
   silently replacing it. Otherwise request `/ai.json` on the page's final origin.
4. Verify the manifest scope covers the page. Follow child routes using C05 until
   the most specific matching description is reached, bounded by D03.

A root catalog may route to products in subdirectories. Publishers without
control of `/ai.json` SHOULD publish their own file and mark their pages:

```html
<link rel="alternate" type="application/json"
      data-ai-first="0.1" href="./ai.json">
```

The href MUST be appropriate for that page's location. `/ai` is not an automatic
fallback. No `/.well-known/` path or custom media type is registered by this spec.
An explicit manifest can be hosted away from its described scope, subject to the
reader's host policy. A reference to another host grants no trust or access.

## D02 Retrieval and representation selection
Public web publications MUST use HTTPS and `application/json` for manifest and
catalog responses. Explicitly configured loopback HTTP is allowed for development
only. Local files have no HTTP MIME header; schema and declared types apply.
Readers MUST check successful HTTP status, Content-Type essence and identity
Content-Encoding before interpreting bytes. A 200 HTML login page is not JSON.
Missing, denied and unavailable are distinct errors. Redirects MAY be refused;
readers following them MUST reapply policy on every hop, cap hops and use the final
URL as the base for relative links. Credentials MUST NOT flow across origins.

Readers MUST obtain a complete catalog inventory before claiming an exhaustive
search. A best-effort reader MAY return known items with explicit partial status.
Selection MUST obey kind, status, product, exact version and requested language.
Descriptions assist relevance selection; a keyword hit is not semantic proof.
Multiple candidates MUST remain visible; readers MUST NOT pick a contradictory
candidate solely by list order. No match and incomplete search MUST be distinct.

When reading an item, select a supported full representation. List order expresses
publisher preference only among equivalent supported full representations. A failed
representation MAY fall back to another full representation with the failure
reported. A digest mismatch invalidates those bytes. Text MUST decode as UTF-8;
code blocks MUST NOT be normalized during retrieval. Summaries, snippets and
LLM-generated responses MUST NOT be described as exact source bytes.

Readers MUST return source, item ID/revision, publication revision, retrieval
location and representation used with the result. HTML anchors and Markdown
fragments are citation aids; 0.1 retrieval obtains the full document and MUST NOT
pretend to extract a fragment. No new chunk format is required.

## D03 Bounds and URL policy
Readers MUST enforce finite bounds before and during parsing and traversal.
The baseline supported envelope is at most 256 KiB per manifest/catalog, 8 MiB
per material, 64 descriptor documents, catalog/route depth 8, JSON nesting 64,
10,000 total items, and 32 MiB total bytes per operation. HTTP operations MUST have
a finite per-request timeout (reference default 10 seconds). Readers MAY impose
stricter caller limits and MUST report limit-exceeded, never silent truncation.
A depth of zero is the entry document; limits include unsuccessful fetch bytes.

Only explicitly authorized roots/origins may be accessed. Local paths MUST remain
inside the caller's root after decoding and symlink resolution. A remote document
MUST NOT trigger local-file reads. HTTP userinfo, non-HTTP schemes, network-path
references, backslashes and control characters in retrieval links MUST be rejected.
Network clients MUST prevent access to loopback/private/link-local/reserved targets
unless a caller explicitly configures a trusted development environment. Validate
the actual connection destination, not only an earlier DNS lookup; use a protected
egress transport or pinned validated addresses. DNS rebinding must not bypass policy.

## D04 Updates and offline copies
Publishers SHOULD stage materials and catalogs before publishing the manifest,
and switch snapshots atomically where possible. Immutable revision directories
are recommended. A reader seeing mixed catalog revisions MUST report mismatch.
It MAY restart a bounded operation, but MUST NOT loop indefinitely.

Readers MUST revalidate mutable remote descriptions on a new operation according
to HTTP cache controls; offline results MUST be labelled offline with freshness
unknown. Version labels alone do not establish freshness. The reference reader
has no persistent cache. Local copies retain identity and relative links; absolute
web scopes may require a republished relative scope for local-root discovery.
Publishers MUST retain source attribution and record a new publication revision
when modifying the copy's metadata.

## D05 Coexistence
If ai.json already serves an unrelated format, a publisher MUST NOT overwrite it
as part of automatic adoption. Publish a distinct direct manifest and use the
marked page link. Readers MUST validate the format discriminator even at the
conventional path and MUST NOT reinterpret another format by guessing its fields.

An explicitly supplied resource root MUST also be covered by the selected
manifest scope; child routing uses that root as its target when applicable.
