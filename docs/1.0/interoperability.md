# Interoperability with adjacent initiatives

AI First is a discovery and description layer. It can point to other standards
without replacing their contracts or granting permission to use them.

| Initiative | Use with AI First |
| --- | --- |
| `llms.txt` | Generate a compact human-readable index from the same item inventory. It remains a companion, not the structured source of truth. |
| OpenAPI | A capability item points to the authoritative operation in an OpenAPI 3.0–3.2 document. The reader validates the locator and never calls it. |
| MCP | A capability item may point to a published tool-description snapshot. A separately configured MCP client owns live negotiation and execution. |
| A2A Agent Card | Publish the card as linked material or an external contract. A2A owns agent identity, skills, and interaction semantics. |
| WebMCP | Describe the web resource and link its interface documentation. The browser environment owns actual tool exposure and user interaction. |
| AI Discovery Endpoint | Link service metadata as a related resource or external contract. It does not expand trusted origins or credentials. |

Use the generic `external` binding when AI First has no dedicated validation
rule. State the contract type and locator meaning in its description and report
validation as not-run when the client lacks that binding. This lets later 1.x
releases add optional bindings without putting unstable protocol details into the
mandatory core.

For system composition, scenarios, provider requirements, and observations,
publish readable plus machine-readable knowledge from one source. Domain-owned
schemas remain authoritative. A generic AI First client retrieves them; a domain
adapter interprets them. Related links do not prove installation, availability,
compatibility, or authorization.

