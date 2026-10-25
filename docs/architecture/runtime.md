# runtime

The web runtime is powered by Starlette and Uvicorn with persistent WebSockets.

### session isolation
Each browser connection initializes an isolated `Session` object. The session maintains its own component tree, active route, reactive state store, and event bindings.

### streamlit-tier granular hot reload
During development (`shadlet dev`), shadlet watches the workspace for Python source modifications using `watchfiles`:
- File system write events are debounced with a minimum cooldown threshold (300ms) to prevent multi-fire churn.
- When changes occur, `session.refresh()` re-evaluates the view tree and generates granular diff patches (`set_prop`, `replace_node`, `insert_child`, `remove_child`).
- Updates are transmitted over the active WebSocket, instantly updating only the changed DOM nodes without resetting client-side state or triggering a full browser refresh.

### disconnect recovery
If the connection is interrupted:
- A full-width banner appears at the top of the interface indicating that the server disconnected.
- The client automatically retries connecting using exponential backoff (starting at 400ms up to 3s).
- Users can also trigger immediate reconnection using the interactive button in the banner.
