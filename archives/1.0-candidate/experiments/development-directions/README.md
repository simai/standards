# Development-directions experiments

Status: executable synthetic experiments, not a normative profile, real service
check or completed Larena/Docara pilot. Implements the first isolated examples in
[the accepted execution direction](../../docs/proposals/2026-09-12-larena-development-directions-review.md).
The [1.0 roadmap](../../docs/1.0/roadmap.md) records the stable target and remaining work.

```sh
python experiments/development-directions/run.py
node experiments/development-directions/client.mjs
python -m unittest discover -s experiments/development-directions -p test_experiments.py -v
python tools/check_candidate02.py
```

Use the existing requirements-0.2.txt environment. No additional dependency,
network service, credentials or model is required. The runner generates temporary
publications, loads them through the unchanged 0.2 reader and reports exact case
outcomes and local read volumes. Temporary files are removed after the run.

## One source, two readable forms

[source.json](source.json) holds synthetic composition, scenario and image-provider
facts. `run.py` produces complete JSON and Markdown representations from the same
value, then publishes them as ordinary knowledge items. No extra manifest field
is introduced. The Markdown includes complete structured content so its meaning
does not silently omit details present in the JSON. The domain adapter interprets
the retrieved JSON; the AI First reader validates, selects and retrieves it only.

## What the examples demonstrate

1. A monolith and remote deployment retain the same provider identity. Location
   changes do not establish or erase installation identity. Publisher declarations
   are explicitly not observed installation proof.
2. A public projection hides private names and contract IDs before publication.
   A restricted inventory gives unknown for an undisclosed prerequisite. An
   authoritative complete inventory with a missing requirement reports missing.
   A scenario naming a protected capability is itself withheld from the public
   publication rather than disclosing it through explanatory prose.
3. A similar image provider can be incompatible; a plausible provider without
   evidence remains unknown. Scoped synthetic evidence can support compatibility
   only for the bound requirements, provider, configuration, tenant and time.
4. Expired, future-dated, wrong-tenant, wrong-revision, wrong-requirement, untrusted,
   failing or undersized observations do not produce compatible results.
5. A publication remains complete even when it has an unvisited related link.
   The related URL is never fetched automatically. System-assessment coverage is
   a different fact from catalog completeness.

## Results and interpretation

[results.json](results.json) records the reproducible outcomes. Unit tests add
counterexamples: changed configuration before expiry, changed requirements,
invalid clocks, injected instructions, ambiguous provider ownership and mutation
isolation between projections. These tests establish only the fixture behavior.

The image and delivery comparisons reuse the same evidence bindings while keeping
format/alpha/size and country/mode/weight rules in their domain adapters. An
independent JavaScript client reproduces the fixed compatible, incompatible and
unknown outcomes without calling the Python adapter. This supports a reusable
evidence-document recipe, but still does **not** justify a new required field or
a universal compatibility language.

## Limits

No actual image processing occurred. A synthetic checker is trusted only by this
fixture's explicit policy. Projection coverage is supplied by a simulated publisher;
these tests do not prove the correctness of real product authorization. There is
no shared credential cache here and no real actor HTTP test in this experiment.
Error/provenance disclosure and actual tenant cache isolation remain to be tested
before promoting any new client behavior. No service switch or business handler
is called, and no frozen candidate/handoff is rewritten.
