# AI First 1.0 scope decision

Date: 2026-09-12  
Status: accepted implementation baseline for the local 1.0 candidate

## Decision

AI First 1.0 will stabilize the proven 0.2 publication model without adding a
required field or a new required profile. Wire version `1.0` will have its own
schemas and readers. Wire versions `0.1` and `0.2` retain their existing meaning
and handlers.

The mandatory manifest remains a resource description with five fields:
`format`, `formatVersion`, `document`, `revision`, and `resource`. Items,
catalogs, routes, access hints, translations, related resources, and capability
descriptions remain optional.

The following are stable optional profiles in 1.0: `knowledge`, `capability`,
`selective-catalogs`, `translations`, and `protected-reading`. The `core` token
continues to identify the base behavior. No workflow engine, service graph,
provider comparison language, evidence ledger, signature system, credential
exchange, or business executor is added.

## Evidence for the decision

The fixed experiments cover monolithic and remote composition, a protected
prerequisite, an assortment scenario, image processing, and delivery. The image
and delivery adapters reuse the same evidence bindings and an independent
JavaScript implementation reproduces the fixed outcomes. Both domains still
need different comparison rules. This proves a useful evidence-document recipe,
but does not prove a universal compatibility language.

All experiment publications use ordinary knowledge items. The required manifest
delta is zero. Related resources remain explicit navigation and are never
installation proof, authorization, or a reason for automatic traversal.

## Integration with other initiatives

AI First describes and locates material. It complements protocols that own
their own contracts:

| Initiative | AI First 1.0 use |
| --- | --- |
| llms.txt | Generate a readable navigation companion from the same publication inventory. |
| OpenAPI | Use a capability contract locator; the OpenAPI document remains authoritative. |
| MCP | Link a published tool-description snapshot; live negotiation and execution remain MCP concerns. |
| A2A Agent Card | Publish or link the card as an external contract/material; A2A owns agent semantics. |
| WebMCP | Describe the page and link its authoritative interface documentation; browser tool exposure remains WebMCP behavior. |
| AI Discovery Endpoint | Link its service metadata as a related resource or external contract without merging trust scopes. |

Emerging protocol names are not added to a closed core enumeration. The
`external` contract binding and ordinary related-resource descriptions preserve
forward compatibility. A later minor release may add an optional binding only
after a stable upstream contract and interoperable fixtures exist.

## Stable compatibility policy

- Editorial corrections with unchanged meaning use a patch release.
- Backward-compatible optional bindings or profiles use a minor release.
- Removed behavior, changed meaning, or incompatible required data use a major
  release with migration and parallel old-version support.
- Unknown optional fields remain ignorable. Unknown tokens in `requires` fail
  closed, so a publisher can declare semantics that must not be approximated.

## Deferred work

Typed installation topology, executable scenario definitions, universal
provider matching, standardized runtime observations, signatures, version
ranges, OAuth clients, and business execution remain outside 1.0. Product
pilots may justify later optional work, but cannot silently change this baseline.
