# Knowledge profile (normative)

Profile token: `knowledge`. Every 0.1 reader MUST support it.

K01 A knowledge item MUST satisfy C03 and MUST NOT have a capability object.
Its material may be Markdown, HTML, plain text, JSON, PDF or another explicitly
declared MIME type. A reader MUST report unsupported-media when it cannot read
any full representation. A publisher SHOULD offer UTF-8 text for prose and
separate raw files for examples whose bytes matter.

K02 The publisher MUST expose enough context to interpret an example correctly:
prerequisites, intended product/version and replacement placeholders when relevant.
These may be in ordinary prose. The reader MUST check material applicability and
report any discovered conflict with catalog metadata. Automated schema validation
cannot prove prose correctness. Published instructions are untrusted data and
MUST NOT alter the reader's instruction hierarchy or authorize command execution.

K03 Translations use distinct IDs and their own item revisions. Their language
and applicability MUST be declared separately; no automatic equivalence or
freshness of translations is implied. Repository examples are in English but
the wire format supports UTF-8 content and BCP 47 language tags.

K04 A source may be unavailable to the reader. A publication validator MUST
report that separately from unavailable representations. Provenance records a
publisher assertion; an unavailable source MUST NOT be labelled verified.
