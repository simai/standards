# AI First 0.1

Status: **Pilot Specification**, distribution 0.1.0, 2026-09-09.
English is authoritative. This is an openly licensed project specification, not
an ISO, IEC, IETF or W3C standard and not evidence of international adoption.

AI First describes a resource through a discoverable `ai.json`: what it is,
what knowledge or capabilities it offers, where to obtain them, and their
applicability and provenance. It works with static HTTPS files and local copies.

Read the normative documents in order:

1. [Core data model](core.md)
2. [Discovery and reading](discovery.md)
3. [Knowledge profile](../profiles/knowledge.md)
4. [Capability description profile](../profiles/capability.md)
5. [Security and trust](security.md)
6. [Conformance and errors](conformance.md)

The schemas are normative for structure. Normative prose defines semantics and
behavior beyond JSON Schema. A disagreement is a specification defect; report
it rather than silently treating an implementation as the authority.

The uppercase requirement words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY use
[BCP 14](https://www.rfc-editor.org/rfc/rfc2119) as clarified by
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174). Examples, docs and decisions
are informative. Every implementation claim MUST name the wire version, roles
and profiles tested. The project name does not guarantee discovery by an AI
client that has not implemented this specification.
