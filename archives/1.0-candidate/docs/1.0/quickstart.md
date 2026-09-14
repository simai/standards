# AI First 1.0 quick start

Create `ai.json` at the resource root:

```json
{
  "format": "ai-first",
  "formatVersion": "1.0",
  "document": "manifest",
  "revision": "2026-09-12-1",
  "resource": {
    "id": "https://example.com/docs",
    "name": "Example documentation",
    "description": "Public product documentation and integration guides.",
    "language": "en",
    "scope": "./",
    "publisher": {"name": "Example"}
  }
}
```

That is a valid resource-only publication. Add items only when the client should
read material:

```json
{
  "id": "https://example.com/docs/getting-started",
  "kind": "knowledge",
  "title": "Getting started",
  "description": "Install and configure the product.",
  "language": "en",
  "revision": "1",
  "status": "published",
  "source": "getting-started.md",
  "representations": [
    {"href": "getting-started.md", "mediaType": "text/markdown"}
  ]
}
```

Put the item in the manifest `items` array. Validate and read it:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-1.0.txt
.venv/bin/python tools/aifirst10.py validate /path/to/publication
.venv/bin/python tools/aifirst10.py read /path/to/publication --id https://example.com/docs/getting-started
node tools/aifirst10.mjs read /path/to/publication --id https://example.com/docs/getting-started
```

For a web page, advertise the manifest explicitly:

```html
<link rel="describedby" type="application/json" data-ai-first="1.0" href="./ai.json">
```

Use catalogs for large inventories, translations only with reviewed shared-work
identity, and capability items only to locate an existing contract. Credentials
are supplied to the reader separately. Discovery never authorizes execution.

