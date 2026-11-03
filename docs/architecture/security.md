# security

shadlet validates connections and messages at the websocket boundary. it does
not provide an authentication provider or an authorization model. applications
remain responsible for verifying who a user is and what they may access.

## connection sequence

1. the browser opens `/ws` and sends a `hello` message.
2. the server validates the origin policy.
3. the server validates the message shape with the shared protocol models.
4. the server negotiates a protocol version.
5. the optional `authenticate` hook runs.
6. an existing session is restored by token, or a new session is created.
7. the server sends the initial render.
8. events, navigation, and pings are accepted only after this point.

the server never sends application state before steps 2-6 succeed.

## origin validation

by default, same-origin browser connections and localhost origins are accepted.
non-browser clients that omit `Origin` are accepted. for production, configure
`WebConfig(allowed_origins=(...))`. `"*"` disables validation and should only be
used behind another enforcement layer.

origin validation is not authentication.

## authentication

pass `authenticate=` to `ui.App`. the hook receives a `ConnectionRequest` with
the origin, host, path, session token, headers, and query parameters. return
`True` to accept. it may be async.

do not log session tokens or authorization headers.

## sessions

session tokens are generated with `secrets.token_urlsafe(32)`. a token restores
the session it was issued for. treat the token as a bearer credential: anyone
who possesses it can resume that session. sessions are in memory only, expire
after `WebConfig.session_ttl` of inactivity while disconnected, and are removed
at shutdown.

## limits

- `max_message_bytes` bounds every websocket frame.
- `max_events_per_second` is a per-session token bucket for events, navigation, and pings.
- `max_sessions` bounds concurrent sessions.
- `handshake_timeout` bounds unauthenticated idle connections.
- queued toasts are capped per session.
- invalid and stale event ids are rejected.

## error responses

browser clients receive short error codes and messages. tracebacks are only
included when `App(debug=True)`. server-side exceptions are logged with the
`shadlet.*` loggers.

## reporting

see `SECURITY.md` at the repository root for the disclosure process.
