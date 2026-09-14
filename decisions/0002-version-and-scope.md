# 0002: Freeze a usable pilot rather than promise universal execution

Status: accepted for 0.1, 2026-09-09.

Wire version is exactly `0.1`; distribution version starts at `0.1.0`. Breaking
wire changes use a new wire version, including during 0.x. Unknown required
profiles block the affected document. Unknown optional fields are ignored.

Core and Knowledge are mandatory reader support. Capability description and
child routing are included, but operation execution, authentication negotiation,
process execution, search APIs, event streams and federation trust are not.
Existing contracts continue to own execution. This closes the discussed paths
without creating a second transport or authorization system.

Discovery supports direct documents, explicit folder roots, page HTML alternate
links marked `data-ai-first="0.1"`, and origin-root ai.json. No parent-directory
probing or implicit metadata inheritance. Child routes select the longest matching
scope; equal-scope competing routes are errors. A document's scope is an assertion,
not proof of ownership. An explicitly linked manifest must still cover the page.

First-party examples and test clients cannot establish independent adoption.
Version 0.1 is a usable pilot specification; international consensus, registered
names and institutional recognition require work outside this local delivery.
