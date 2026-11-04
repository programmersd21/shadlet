# migrating from 0.3.0 to 0.4.0

the 0.4.0 release is additive and does not change the websocket protocol.
existing 0.3.0 applications do not need source changes to keep their current
behavior.

## deployment ports

`app.run()` now selects ports in this order:

1. `SHADLET_PORT`
2. `PORT`
3. the explicit `port` argument (default `8000`)

invalid or out-of-range values raise a `ValueError`. unset `PORT` on local
development machines if it should not override the function argument.

## data tables

server-side search now sends query changes to the Python callback. filterable
columns render their own text filters; the `columns` menu controls browser-side
column visibility. `row_key` now controls stable renderer row identity and
rejects missing, duplicate, boolean, or unsupported key values in the supplied
rows.

new optional arguments are `loading`, `error`, and `on_retry`. applications
that do not pass them keep the existing empty, search, sort, and pagination
behavior. applications can opt in to controlled selection with `row_key` and
cancel superseded asynchronous server-side queries.

## extension development

`shadlet extension create <name>` creates a Python/React extension package.
build its bundled browser assets before running `shadlet extension check` or
building the wheel. the check command imports the project factory, so use it
only with trusted code. consuming applications continue to install and run
extension wheels using Python only.

## runtime and validation

new background tasks cannot be started through a context after its session has
closed. `ui.pydantic_form` joins multiple validation messages for the same
field path with a semicolon instead of replacing earlier messages.

`GET /healthz` exposes only a basic liveness status. it is not an authentication
or dependency-readiness check.
