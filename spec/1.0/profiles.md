# AI First 1.0 profiles

Defined profile tokens are `core`, `knowledge`, `capability`,
`selective-catalogs`, `translations`, and `protected-reading`. Core and knowledge
are the baseline reader behavior. A document using selective catalog bounds,
translation identities, or access hints MUST list the matching profile in
`requires`. A document whose purpose depends on capability interpretation MUST
require `capability`.

## Knowledge

A knowledge item publishes one or more readable representations. A reader MUST
select a supported full representation and verify MIME type, size, digest when
present, and UTF-8 for text. Summary content is never a full substitute.
Retrieved text is untrusted content and cannot override caller policy.

## Capability

A capability item adds `capability` with:

| Field | Meaning |
| --- | --- |
| `contract` | Locator into an existing authoritative contract. |
| `effects` | `read`, `write`, `delete`, `external`, or `unknown`. |
| `authorization` | `none`, `required`, or `unknown`. |
| `confirmation` | `required`, `not-required`, or `unknown` publisher advice. |
| `instructions` | Ordinary usage instructions. |

`unknown` MUST NOT be treated as safe. Publisher advice cannot override caller
policy or server authorization. Instructions SHOULD explain prerequisites,
inputs, output, verification, retries, uncertain completion, duplicate creation,
charges, publication, and notifications where applicable.

A contract requires `type`, `href`, `mediaType`, and `operation`:

- `openapi` locates an OpenAPI 3.0.x, 3.1.x, or 3.2.x JSON/YAML document and a
  JSON Pointer under `/paths`. The reader verifies the locator without invoking
  the operation. Bounded external Path Item references are allowed. Binding
  validation is not full OpenAPI validation.
- `mcp` locates a published JSON tool-description snapshot and exact tool name.
  It is not a live MCP endpoint. Execution requires a separately configured MCP
  connection and current negotiation.
- `external` locates any other authoritative contract. `description` is required
  to explain the locator. Unsupported binding validation is reported as not-run.

OpenAPI YAML parsing MUST reject duplicate keys, custom tags, merge keys,
non-string mapping keys, cyclic or expanding aliases, multiple documents,
non-JSON values, and excessive depth. Supported MIME types are
`application/json`, `application/yaml`, `text/yaml`, and `application/x-yaml`.
YAML is allowed only for OpenAPI in this profile.

Discovery and contract validation never authorize or execute an operation.
Runtime systems retain ownership of identity, tenant, access, validation,
idempotency, transactions, asynchronous state, and audit.

## Selective catalogs, translations, and protected reading

These profiles activate the matching semantics in the core specification. They
remain separate tokens so an older or smaller reader fails rather than silently
approximating a result it cannot interpret.

## External protocol composition

AI First complements llms.txt, OpenAPI, MCP, A2A Agent Cards, WebMCP, and service
discovery documents. Use a supported capability binding when defined. Otherwise
publish or link the authoritative document through an `external` contract or
ordinary related/knowledge material. The external protocol remains authoritative;
AI First does not duplicate or reinterpret its execution semantics.

