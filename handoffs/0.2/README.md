# AI First 0.2 product pilot handoffs

These files are for the existing product executors. The user transfers the links;
the standard task does not locate threads, send messages, create product tasks or
edit product repositories.

- [Docara handoff](docara.md)
- [Larena handoff](larena.md)
- [Return receipt schema](../../schemas/0.2/pilot-result.schema.json)
- [Candidate inventory](../../conformance/0.2/candidate.json)

Before accepting a return, run:

```sh
python tools/check_candidate02.py
python tools/check_pilot02.py /path/to/pilot-result.json /path/to/artifact-bundle
```

The second command reads only the supplied files and advertised documentation;
it does not execute commands contained in the receipt. It checks publication
compatibility and leaves final scenario acceptance pending explicit review.
Actual reproducibility and actor/build evidence must be reviewed before updating
pilot status. See [pilot status](../../conformance/0.2/pilots/status.json).
