# migrating from 0.4.0 to 0.5.0

the 0.5.0 release is additive. existing pages, components, protocol messages,
and extension manifests continue to work after upgrading.

## package versions

update applications and extensions to require `shadlet>=0.5.0`. the scaffolded
extension dependency range now has an upper bound for the current minor series,
for example `shadlet>=0.5.0,<0.6.0`.

## icons

the manually maintained icon subset has been replaced by the complete generated
Lucide catalogue, pinned to `lucide-react` 0.577.0.

- `ui.Icon("name")` now accepts every canonical Lucide icon name.
- `ui.icons.arrow_up_right(...)` is a generated namespace for the same
  catalogue, including aliases.
- invalid icon names fail during component construction. They are no longer
  silently replaced by a different icon.
- `ui.Button(icon=...)`, `MenuItem`, `TabItem`, and `SidebarItem` validate icon
  names in Python.

see the [icons guide](../guides/icons.md) for discovery and regeneration.

## uploads and storage

`UploadedFile` gains `safe_filename` and `save_to(storage, key=...)`.

```python
from pathlib import Path

import shadlet as ui

storage = ui.LocalStorage(Path("var/uploads"))


@ui.app.upload("/avatar")
async def avatar(upload: ui.UploadedFile):
    stored = upload.save_to(storage, key=f"avatars/{upload.safe_filename}")
    return {"stored": stored.key, "size": stored.size}
```

`LocalStorage` provides safe relative keys, atomic writes, streaming writes,
overwrite control, and a maximum byte limit. It is a local-filesystem backend,
not a distributed or durable cloud-storage service.

## runtime limits

`WebConfig` adds these validated settings:

| setting | default | purpose |
|---|---:|---|
| `max_event_payload_bytes` | 256,000 | maximum serialized event payload |
| `max_tree_nodes` | 20,000 | maximum serialized component nodes per render |
| `max_tree_depth` | 128 | maximum serialized component tree depth |

renders that exceed a tree limit fail with a generic client-facing
`render_error`; details are logged and only exposed in debug mode.

## routing

request paths are normalized and percent-decoded once. malformed percent
escapes, invalid UTF-8, encoded path separators, NUL bytes, backslashes, and
dot segments are rejected. route parameters are decoded exactly once.

## extension commands

`shadlet extension build` installs browser dependencies, runs the extension's
Node.js build, then runs `shadlet extension check`. `shadlet extension info`
prints manifest metadata and packaged asset sizes without starting an
application.

extensions remain trusted application code. Node.js is required only by the
extension author running the build command; applications consume the packaged
assets with Python only.
