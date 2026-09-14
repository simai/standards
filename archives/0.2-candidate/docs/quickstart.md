# Add AI First to a project

Start with one file next to existing documentation. This example assumes README.md
is the full, public English material you intend to expose:

```json
{
  "format": "ai-first",
  "formatVersion": "0.1",
  "document": "manifest",
  "revision": "1",
  "resource": {
    "id": "urn:example:my-project",
    "name": "My Project",
    "description": "Setup instructions and usage examples for My Project.",
    "language": "en",
    "scope": "./",
    "publisher": {"name": "My Organization"}
  },
  "items": [
    {
      "id": "urn:example:my-project:readme",
      "kind": "knowledge",
      "title": "Getting started",
      "description": "Install the project and run its basic example.",
      "language": "en",
      "revision": "1",
      "status": "published",
      "source": "./README.md",
      "representations": [
        {"href": "./README.md", "mediaType": "text/markdown"}
      ]
    }
  ]
}
```

Replace example identities, descriptions and publisher with your own stable
values. Use HTTPS IDs you control or another valid absolute URI namespace. A
random URL is not proof of identity. Do not put credentials or host-local paths
in the document. Add `appliesTo` when publishing version-specific instructions.

## Validate and read
In a copy of this standard repository:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/aifirst.py validate examples/minimal
.venv/bin/python tools/aifirst.py read examples/minimal --version 3.0
.venv/bin/python tools/aifirst.py list examples/catalog --query authentication
```

To validate your project, replace examples/minimal with its directory. The reader
only accesses files within that directory. Calling it against a repository root
does not make private files safe to publish: review the actual export separately.

## Publish static files
Copy the approved ai.json and its linked public files into your static output.
Serve descriptor files as application/json and Markdown as text/markdown. Use
HTTPS. No API server or AI model is needed. Share the root URL ending in `/`, or
share the exact manifest with readers configured for direct-manifest mode.

To try a loopback server locally, run in a separate terminal:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory examples/minimal
```

Then:

```sh
.venv/bin/python tools/aifirst.py read http://127.0.0.1:8765/ --allow-loopback --version 3.0
```

Your Python HTTP server must serve .md as text/markdown. If it does not, configure
its MIME mapping or use the test server in the suite. Stop the server with Ctrl-C.
The `--allow-loopback` exception is for this development test, not public hosting.

## Introduce catalogs or actions later
Use examples/catalog for a split inventory. Its catalogs share resourceId and
publication revision with ai.json. Use examples/service to link an existing
OpenAPI operation. Discovery never grants permission to execute it.

Before adoption, read the [publisher guide](publisher.md),
[reader guide](reader.md), [specification](../spec/README.md) and
[licensing policy](../LICENSE.md). 0.1 is usable for pilots; record the wire
version and expect explicit migrations for future breaking versions.
