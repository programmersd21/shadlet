# deployment

shadlet applications are ordinary ASGI applications. the runtime uses
Starlette and Uvicorn and communicates over a WebSocket at `/ws`.

## production startup

`app.run()` is intended for local development. in production run the ASGI app
with Uvicorn or another ASGI server and a configurable number of workers:

```python
# server.py
import main

app = main.app
```

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
```

Sessions are stored in memory and are scoped to one worker. if you run multiple
workers, a reconnect may land on a different worker and start a new session.
either use a single worker or place session affinity in front of the workers.

## reverse proxy

the proxy must forward WebSocket upgrades and preserve the `Host` and `Origin`
headers. nginx example:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 3600s;
}
```

Caddy forwards WebSockets automatically:

```caddyfile
app.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

## origins

set `WebConfig(allowed_origins=(...))` to the public origin of the application.
origin validation is not authentication. use the `authenticate` hook or an
upstream auth proxy for access control.

## static assets

renderer assets are served from `/_shadlet_assets`. application assets placed in
`assets/`, or in `SHADLET_ASSETS_DIR`, are served from `/assets`. neither path
can escape its configured directory.

## health and shutdown

the runtime closes sessions and cancels their background tasks during ASGI
lifespan shutdown. send `SIGTERM` and give the server a short grace period so
clients receive a clean close. sessions do not survive a restart.
