# deployment

shadlet applications are ordinary ASGI applications. the runtime uses
Starlette and Uvicorn and communicates over a WebSocket at `/ws`.

## production startup

`app.run()` is intended for local development. it reads `SHADLET_PORT` first,
then the platform-standard `PORT`, then its `port` argument (default `8000`).
each value must be an integer from `0` to `65535`. in production run the ASGI
app with Uvicorn or another ASGI server and a configurable number of workers:

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
background tasks are owned by the worker that started them; they are cancelled
when the session closes and do not survive a process restart. uploaded file
contents are bounded and held in memory for the request. persist files to
application-managed storage if they must outlive the request.

## health check

`GET /healthz` returns only `{"status":"ok"}`. it is a lightweight process
liveness check; it does not expose session state or prove that external
services are available.

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

## Docker and Render

The repository includes a multi-stage, non-root Docker example in
`examples/deployment/Dockerfile` and a Render Blueprint in `render.yaml`. The
Docker build compiles the React renderer, installs the locked Python project,
and runs Uvicorn with one worker. Render supplies `PORT`; the container uses it
for both Uvicorn and its `/healthz` check.

From the repository root, build and run the image locally:

```bash
docker build -f examples/deployment/Dockerfile -t shadlet-example .
docker run --rm -p 8000:8000 -e PORT=8000 shadlet-example
```

For Render, connect a fork or repository containing the root-level
`render.yaml` and deploy its Blueprint. Review the service name and plan in the
Blueprint before applying it. The example uses the default same-origin policy;
set `WebConfig(allowed_origins=(...))` when deploying behind a proxy with a
different public origin. Origin validation is not authentication.

The Docker example is a single-process reference deployment, not a
multi-worker scaling recipe.  sessions remain process-local; use one
worker unless the application adds session affinity and accounts for
process-local background-task and upload behavior.

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
clients receive a clean close. sessions do not survive a restart. configure
production authentication with `App(authenticate=...)` or an upstream auth
proxy; origin validation is not authentication.
