# SIMAI standards 1.1.0

Two complementary, maintainer-supported stable standards for project adoption.
AI First describes discoverable knowledge and existing capabilities. Standard
Contract describes the rules objects select, inherit and use, with pinned local
dependencies and a separate lifecycle profile. [SIMAI standards](standards/README.md)
in that envelope apply across SIMAI sources: `simai.linkage` and
`simai.change-lifecycle` 1.1.0.

- [AI First 1.0 specification](spec/1.0/README.md) and [reader guide](docs/1.0/quickstart.md).
- [Standard Contract 1.0.0](standard-contract/1.0/README.md) and [lifecycle](standard-contract/lifecycle/README.md).
- [Adoption and migration](docs/releases/adoption.md).
- [SIMAI standards: linkage and change lifecycle](standards/README.md).
- [Release notes](docs/releases/v1.1.0.md), [release status](RELEASE-STATUS.md), [governance](GOVERNANCE.md).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-1.0.txt
.venv/bin/python tools/aifirst10.py --help
.venv/bin/python standard-contract/1.0/contract.py standalone standard-contract/1.0/examples/portable/button.md.standards.json
.venv/bin/python standard-contract/lifecycle/lifecycle.py --help
.venv/bin/python tools/verify_release.py
```

Python 3.10+ is required. JavaScript reader tests require Node.js 22+; set
`AI_FIRST_NODE` if it is not on PATH. The Python reader provides the broader
transport implementation; the JavaScript reader tests the documented core subset.

Stable means a versioned contract with maintained tools, tests and compatibility
commitments. It does not certify arbitrary objects, complete the Docara/Larena
pilots, establish independent interoperability or imply international recognition.
No discovery document grants permission to execute business actions.

Historical AI First 0.1/0.2, the 1.0 release candidate and Standard Contract drafts
remain available. [Archive rules](archives/README.md) explain exact-byte verification.
The root `ai.json` remains a backward-readable 0.1 publication of this repository's
current knowledge; its wire version does not select the released standard edition.
