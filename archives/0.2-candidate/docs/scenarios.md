# Scenarios that define the first release

## Publisher journey
1. Choose the resource root and who owns the exported knowledge.
2. Write a small ai.json with purpose, identity, scope, publisher and revision.
3. List existing materials inline. Split into catalogs only when needed.
4. Declare exact applicability and full representations; preserve source links.
5. Validate structure, then the staged publication. Review visibility and meaning.
6. Publish ordinary files together; update revision and digests on change.
7. Give readers the root or explicit manifest; mark pages when root access is absent.

No build system is required. For generated docs, the exporter reads the existing
authoritative content model and outputs descriptors deterministically. It must
not maintain a parallel manually edited copy of operation schemas.

## Reader journeys and outcomes
| Scenario | Start | Successful outcome | Important failure |
| --- | --- | --- | --- |
| Find an authentication guide | Documentation root and product version | Exact applicable material with source | Missing version is not universal |
| Understand a service action | Service root and desired action | Existing contract locator and usage instructions | No access or unsupported binding |
| Explore a local package | Caller-authorized directory | Same relative files without network | Path or symlink escape |
| Read a product on a shared domain | Deep page | Marked manifest or root-to-child route | Contradictory scope |
| Update published knowledge | New staged snapshot | Consistent catalogs and material digests | Mixed revisions |
| Read a multilingual resource | Requested language | Explicit language-matched item | Translation absent or stale |

The included products and operations are fictional reproducible examples, not
claims of integrations with Docara, Larena or external publishers. Actual product
adoption should reuse these paths with real content and record its own evidence.
