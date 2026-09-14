# AI First 1.0 stable promotion gate

The `1.0.0-rc.1` candidate is locally conformant and usable by product pilots.
Stable `1.0.0` requires the same frozen candidate plus accepted Docara and Larena
pilot evidence. This requirement prevents a version label from overstating the
evidence available for the contract.

Run the read-only gate from the repository root:

```sh
python tools/check_stable10.py
```

The gate requires:

- a passing immutable candidate lock;
- every recorded local verification check to pass;
- a receipt and artifact bundle for each product;
- an accepted implementation result and evidence review for each product;
- verified publication compatibility for each product;
- all required pilot scenarios to pass.

The checker reads returned bundles and validates their hashes and publications.
It does not execute recorded commands, edit a product repository, promote the
version, publish a release or contact an external community.

After both pilot returns are reviewed, update
`conformance/1.0/pilots/status.json` with repository-relative receipt and bundle
paths, set `implementation` and `evidenceReview` to `accepted`, and set
`compatibility` to `verified`. A passing gate is evidence that promotion may be
prepared; it is not the promotion or public release itself.
