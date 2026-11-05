# configuration

configuration is passed to `ui.App(...)` and to the cli. no separate config file
is required.

## application

```python
import shadlet as ui

app = ui.App(
    "my app",
    theme="system",
    debug=False,
)
```

| argument | default | description |
|---|---|---|
| `title` | `"shadlet app"` | document title and app heading |
| `icon` | `None` | URL or file in the application `assets/` directory (or `SHADLET_ASSETS_DIR`) |
| `theme` | `"light"` | `light`, `dark`, or `system` |
| `debug` | `False` | include tracebacks in render and handler errors |
| `version` | package version | version reported in the `init` message |
| `toaster` | `True` | mount the toast host |
| `web` | `WebConfig()` | websocket limits and origin policy |
| `authenticate` | `None` | connection authentication hook |

## web runtime

```python
from shadlet.web.config import WebConfig

app = ui.App(
    "my app",
    web=WebConfig(
        allowed_origins=("https://app.example.com",),
        session_ttl=1800,
        max_sessions=500,
        max_message_bytes=500_000,
        max_event_payload_bytes=200_000,
        max_tree_nodes=10_000,
        max_tree_depth=64,
        max_upload_bytes=10_000_000,
        max_events_per_second=100,
    ),
)
```

| field | default | description |
|---|---|---|
| `allowed_origins` | `None` | same-origin + localhost by default; set explicit origins in production |
| `session_ttl` | `3600` | seconds an idle disconnected session is retained |
| `max_sessions` | `1000` | maximum concurrent in-memory sessions |
| `max_message_bytes` | `1000000` | maximum websocket message size |
| `max_event_payload_bytes` | `256000` | maximum serialized event payload |
| `max_tree_nodes` | `20000` | maximum component nodes in one rendered tree |
| `max_tree_depth` | `128` | maximum component tree depth |
| `max_upload_bytes` | `10000000` | maximum combined file bytes accepted by upload endpoints |
| `max_events_per_second` | `200` | per-session rate limit for events, navigation, and pings |
| `handshake_timeout` | `10` | seconds allowed for the `hello` message |
| `sweep_interval` | `30` | seconds between expired-session sweeps |

`allowed_origins=("*",)` disables origin validation. it must be the only entry
in the tuple and should only be used when a proxy or another layer enforces the
policy. file-backed icons are served only from the public application assets
directory or shadlet's own assets; arbitrary local files are not exposed.
render-tree limits protect the server from oversized or deeply nested pages;
limit failures return a generic `render_error` and are logged.

## authentication

`authenticate` receives a `ConnectionRequest` before a session is created or
restored. return `True` to accept the connection.

```python
from shadlet.web.config import ConnectionRequest


def authenticate(request: ConnectionRequest) -> bool:
    return request.headers.get("authorization") == "Bearer secret"


app = ui.App("my app", authenticate=authenticate)
```

The hook may be async. exceptions raised by the hook reject the connection and
are logged server-side.

## environment variables

| variable | description |
|---|---|
| `SHADLET_PORT` | highest-priority port override for `app.run()` |
| `PORT` | platform port override used when `SHADLET_PORT` is unset |
| `SHADLET_RELOAD` | enable the development watcher |
| `SHADLET_ASSETS_DIR` | directory served at `/assets` |

`app.run()` uses `SHADLET_PORT` before `PORT`, then the explicit `port`
argument. configured ports must be integers between `0` and `65535`.
`GET /healthz` returns only `{"status":"ok"}` for process liveness checks.
