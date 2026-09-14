# AI First 1.0 product pilot handoffs

These files are for the existing product executors. The user transfers the links;
the standard task does not locate threads, send messages, create product tasks or
edit product repositories.

- [Docara handoff](docara.md)
- [Larena handoff](larena.md)
- [Return receipt schema](../../schemas/1.0/pilot-result.schema.json)
- [Candidate inventory](../../conformance/1.0/candidate.json)

Before accepting a return, run:

```sh
python tools/check_candidate10.py
python tools/check_pilot10.py /path/to/pilot-result.json /path/to/artifact-bundle
python tools/check_stable10.py
```

The second command reads only the supplied files and advertised documentation;
it does not execute commands contained in the receipt. It checks publication
compatibility and leaves final scenario acceptance pending explicit review.
Actual reproducibility and actor/build evidence must be reviewed before updating
pilot status. See [pilot status](../../conformance/1.0/pilots/status.json).
The final command reports whether all evidence required for stable `1.0.0`
promotion is present. See the [stable promotion gate](../../conformance/1.0/stable-promotion.md).
