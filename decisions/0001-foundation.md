# 0001: A small JSON entry document

Status: accepted for the 0.1 pilot specification, 2026-09-09.

## Problem and options
Publishers need a predictable entry point for static knowledge, local packages
and links to existing operations. Readers need provenance and bounded traversal.

WoT Thing Description 1.1 is an important existing foundation for describing
physical and virtual entities and their interactions. Its JSON-LD model offers
semantic integration. A WoT profile could reuse that vocabulary, but this pilot
would still need a knowledge catalog, publication revisions, local packaging and
discovery rules. See the [W3C Recommendation](https://www.w3.org/TR/wot-thing-description11/).

Choose a small JSON envelope for the pilot. Reuse JSON Schema for structure and
OpenAPI operation references for HTTP capabilities. A future WoT adapter can
link or transform descriptors; 0.1 does not claim WoT or JSON-LD conformance.
This is a scoped design decision, not proof of a gap in every existing standard.

## Scenario comparison
| Criterion | WoT-based profile | Selected JSON envelope |
| --- | --- | --- |
| Static guide and local package | Needs a knowledge profile | Direct item with representations |
| Existing HTTP operation | Could map interaction forms | Retains existing operation via JSON Pointer |
| Graph semantics | Existing JSON-LD foundation | Optional future adapter |
| Reader prerequisites | WoT/profile semantics | JSON plus this bounded contract |

The same static and capability examples are the evaluation inputs. Only the JSON
candidate is implemented; no empirical head-to-head WoT implementation result is
claimed. Revisit if independent pilots show a useful WoT mapping with less burden.

## Consequences
ai.json is the conventional filename; /ai has no automatic fallback or distinct
semantics. A direct manifest URL may have any name. No well-known URI, custom
media type or link relation registration is claimed. This follows the distinction
between a project convention and [RFC 8615 registration](https://www.rfc-editor.org/rfc/rfc8615).

The standard is independent of SIMAI, Docara, Mirai and any AI vendor. The
reference implementation is optional and does not define the standard by itself.

## Collision and overlap check
The primary-source review also found an AI Discovery Endpoint Internet-Draft and
AI Discovery Files using ai.json with different semantics. See
[standards-landscape](../docs/standards-landscape.md). Keep the discussed filename
as a convention, require format recognition, and support explicit alternate file
locations. The choice is usable for the pilot without asserting exclusive naming
or unproven international novelty.
