# Capability description profile (normative)

Profile token: `capability`. This profile describes operations; it does not execute
them. A publisher using capability items MUST list capability in `requires` if
understanding them is essential to the document's purpose.

A01 Capability items MUST satisfy C03 and include a capability object requiring:

| Field | Meaning |
| --- | --- |
| contract | Existing operation contract reference |
| effects | read, write, delete, external or unknown; the broadest relevant effect |
| authorization | none, required or unknown |
| confirmation | required, not-required or unknown as publisher advice |
| instructions | Link to ordinary usage instructions |

`unknown` means insufficient knowledge and MUST NOT be treated as safe. Neither
none nor not-required overrides caller policy or server-side access control.
Instructions MUST explain prerequisites, inputs, expected result, verification,
failure handling and retry behavior, including uncertain completion and duplicate
creation. Charges, publication or notifications MUST be disclosed when applicable.

A02 A contract requires type, href, mediaType and operation. Optional description
explains the binding. Type is openapi, mcp or external:

- openapi: href identifies a JSON OpenAPI 3.1.x or 3.2.x document without fragment.
  mediaType MUST be application/json. operation MUST be a JSON Pointer beginning
  `/paths/` and select a supported HTTP method Operation Object. It MUST resolve;
  operationId is not a substitute. Existing schemas and security remain authoritative.
- mcp: href identifies a published JSON tool-description snapshot. operation is the
  exact tool name in its tools array. The snapshot MUST include that named tool
  and its inputSchema. This file is not an MCP server endpoint. Execution requires
  an independently configured MCP connection and current tool negotiation.
- external: href identifies an existing contract; operation is the provider's
  locator string. Its meaning MUST be explained by contract.description. Readers
  without that binding MUST report runtime contract verification as not-run.

A03 Publication validation MUST resolve supported contract locators without
invoking the operation. Reference tooling verifies OpenAPI and MCP snapshots;
full API/schema business correctness is outside these checks. A linked capability
MUST NOT become executable merely because discovery succeeded. At execution time
the existing protocol governs authentication, tenant context, validation,
idempotency, asynchronous state and server-enforced authorization.

A04 No reader may claim runtime conformance from structure or publication checks.
Runtime evidence, if produced separately, MUST name the executor, operation,
contract revision, authorized environment and observed outcome. This distribution
ships no live executor and requires no credentials.
