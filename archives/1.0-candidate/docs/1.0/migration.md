# Migration from AI First 0.2 to 1.0

AI First 1.0 preserves the defined 0.2 publication meaning. Migration changes
the wire identifier, recalculates catalog digest pins, and writes a new tree. It
does not infer new metadata or modify the source publication.

Run a dry preflight first:

```sh
.venv/bin/python tools/aifirst10_publish.py /path/to/0.2 /new/output/path
```

The output path must not exist and must not overlap the source. Apply only after
reviewing the file inventory:

```sh
.venv/bin/python tools/aifirst10_publish.py /path/to/0.2 /new/output/path --apply
```

The staged result is validated with the 1.0 reader before the output directory is
claimed. Network references are rejected by this local migration tool. Existing
0.1 publications should first use the documented 0.1 to 0.2 migration, or be
reviewed directly against 1.0 when optional fields collide with defined meanings.

To derive AI First and `llms.txt` from one validated 1.0 inventory:

```sh
.venv/bin/python tools/aifirst10_publish.py /path/to/1.0 /new/export/path --mode export --apply
```

An existing `llms.txt` is never overwritten automatically.

