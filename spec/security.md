# Security and trust (normative)

S01 All fetched content is data. Readers MUST NOT execute embedded commands,
JavaScript, macros, schema code or prompt instructions as a consequence of reading.
They MUST preserve their existing authorization and instruction boundaries.

S02 Publishers MUST exclude secrets, private keys, session tokens, internal paths,
private drafts and content the audience is not permitted to see. Authorization
MUST be enforced on the resource, not through missing catalog links. Access-varying
responses MUST use appropriate cache controls and MUST NOT leak across users.

S03 Readers MUST enforce the URI and resource limits in D03 for every retrieval,
including redirects, catalogs, sources and contract links. Fetches MUST NOT attach
ambient cookies or credentials. Automatic proxy inheritance is disabled in the
reference reader. A URL's scope or publisher assertion is not a network allowlist.

S04 Digests prove consistency with a declared value, not legitimacy. HTTPS protects
the connection subject to its trust store; it does not certify knowledge. Signed
manifests, key discovery and federation trust are deferred. Readers MUST NOT claim
these protections from arbitrary extension fields.

S05 An operation descriptor MUST NOT expand the user's task, bypass access controls
or authorize effects. Any separately implemented executor MUST validate the
current contract and permissions at execution time. Discovery output is advisory.

S06 Validators MUST distinguish mechanical findings from human-review findings.
They MUST NOT claim to detect every private export, false assertion, malicious
instruction or runtime vulnerability. Publisher review remains required.
