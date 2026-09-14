# Contributing

All repository content and proposals must be in English. Other languages are
welcome as separately identified example content or future translations; English
remains the authoritative specification.

Start with a scenario, expected outcome and observed failure. Identify affected
requirement IDs (C01, D01, etc.) and explain why an existing mechanism is inadequate.
Do not propose a new required backend, graph engine or model vendor for the core.

For changes, update prose, schemas, examples, tests and changelog together. Run:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_repository.py
```

Use the virtual environment from docs/quickstart.md. Include the actual commands,
results, runtime version and untested requirements. Do not claim independently
verified interoperability from code and tests authored in one implementation team.
No secrets or customer-private data belong in contributions.

By submitting a contribution, you offer it under the repository's MIT License
and confirm you are entitled to do so. The editor records acceptance decisions
under GOVERNANCE.md. Public contribution infrastructure is not provisioned by
this local initial delivery.
