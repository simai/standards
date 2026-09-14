# Relationship to existing work

Reviewed on 2026-09-09. This is a bounded primary-source comparison, not an
exhaustive novelty, patent or trademark search.

| Source | Reuse or boundary |
| --- | --- |
| [JSON](https://www.rfc-editor.org/rfc/rfc8259) | Serialization, with stricter duplicate-key and Unicode handling |
| [URI syntax](https://www.rfc-editor.org/rfc/rfc3986) | Relative resolution and absolute identifiers |
| [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | Structure validation; not proof of knowledge truth |
| [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) | Existing operation contracts remain authoritative |
| [WoT Thing Description 1.1](https://www.w3.org/TR/wot-thing-description11/) | Relevant self-description foundation; see decision 0001 |
| [AI Discovery Endpoint draft-01](https://datatracker.ietf.org/doc/html/draft-aiendpoint-ai-discovery-01) | Overlapping service discovery proposal; not the AI First wire format |
| [AI Discovery Files](https://github.com/BSolveIT/ai-discovery-files) | Already uses ai.json for machine-readable AI usage permissions |

The AI Discovery Endpoint document is an Internet-Draft dated July 2026. It
proposes /.well-known/ai and a service/capabilities description, with a different
processing model. AI First 0.1 instead focuses on portable local/static knowledge
inventories and references to existing execution contracts. This distinction is
a design choice; no claim is made that the other proposal could not be extended.
A future adapter should map semantics explicitly and retain any information loss.
No interoperability or registry recognition is inferred from similar names.

AI Discovery Files assigns a different meaning to ai.json. Keep format recognition
mandatory and use a directly linked alternate filename when paths collide. Neither
project's use establishes exclusive ownership of the path. AI First does not
replace robots.txt, AI-use policies or legal permissions with its access metadata.
