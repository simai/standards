# AI First 1.0.0-rc.1

Status: local release candidate; no public release.

This candidate moves the stable target to wire version `1.0` while preserving
the proven 0.2 semantics and small mandatory manifest. It adds a self-contained
specification, separate JSON schemas and Python/JavaScript handlers, a safe local
0.2-to-1.0 migration, joint AI First/llms.txt export, fixed cross-client cases,
actor-filtered HTTPS checks, and product handoffs.

No mandatory core field or new profile was added. System composition, executable
scenarios, provider matching, runtime evidence, signatures, OAuth, and business
execution remain outside the core. OpenAPI and MCP bindings remain supported;
other initiatives can be linked through ordinary material or an explained
external contract.

Stable promotion still requires candidate acceptance and honest recording of
applicable Docara/Larena pilot results. The release candidate is usable for local
integration and compatibility work. Public distribution and outreach require a
separate action.
