# runtime

The web runtime is powered by Starlette and Uvicorn with persistent WebSockets.

### connection lifecycle

Each connection starts with a `hello` message. The server validates the origin,
the message shape, the protocol range, and the optional authentication hook
before restoring or creating a session and sending the initial render. Invalid
connections are closed with a protocol close code.

### session isolation

Each browser session owns a `Session` object with its own component tree,
active route, reactive state store, event bindings, and task set. Sessions are
keyed by an unguessable token. A reconnect that presents a valid, unexpired
token reattaches the new transport to the existing state.

Sessions are in memory and do not survive a server restart. They expire after
`WebConfig.session_ttl` of inactivity while disconnected. A background sweep
closes expired sessions and cancels their tasks.

### event ordering and limits

Events and navigation messages carry a sequence number. Duplicate or stale
messages are ignored. Each session also enforces a token-bucket event rate
limit and a maximum websocket message size. Render and handler failures are
reported as protocol errors; tracebacks are only included in debug mode.

### task management

Toast delivery, scheduled flushes, navigation, and other background work are
tracked per session. Closing a session cancels outstanding tasks so they cannot
outlive the connection.

### streamlit-tier granular hot reload

During development (`shadlet dev`), shadlet watches the workspace for Python
source modifications using `watchfiles`:

- File system write events are debounced with a 300ms cooldown.
- When changes occur, `session.refresh()` re-evaluates the view tree and
  generates diff patches.
- Updates are transmitted over the active WebSocket without resetting
  client-side state or triggering a full browser refresh.

### disconnect recovery

If the connection is interrupted:

- A full-width banner appears at the top of the interface.
- The client retries with exponential backoff (400ms up to 3s).
- The user can trigger an immediate reconnect from the banner.
- The rendered application is inert while disconnected; interactions are not
  queued or replayed after reconnect.
- The renderer requests a resync when a patch fails or an update sequence gap
  is detected.
