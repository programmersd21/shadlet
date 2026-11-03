# protocol

the protocol is versioned json. it represents component trees, ids, props,
children, events, state updates, patches, navigation, errors, and toasts.

## handshake

the first message from the browser is always `hello`:

```json
{
  "type": "hello",
  "protocol_min": 1,
  "protocol_max": 1,
  "path": "/",
  "token": null,
  "platform": "web"
}
```

the server validates the message, negotiates the highest common protocol
version, checks the origin and optional authenticator, restores or creates a
session, and only then sends `init`.

## versions

`PROTOCOL_VERSION` and `SUPPORTED_PROTOCOL_VERSIONS` are defined in
`shadlet.protocol.version` and mirrored in
`packages/renderer/src/protocol/schema.ts`.

## contract fixtures

`packages/renderer/src/protocol/fixtures.json` contains representative messages.
both sides validate the same fixtures in their test suites:

- python: `tests/unit/test_protocol_contract.py`
- typescript: `src/protocol/__tests__/contract.test.ts`

## message types

server to client: `init`, `update`, `navigation`, `toast`, `error`, `pong`.
client to server: `hello`, `event`, `navigate`, `ping`.

callbacks are never serialised. event ids map to python callbacks server-side.
unknown or removed message types are rejected.

## sequencing

client event and navigation messages carry a monotonically increasing `seq`.
duplicate or stale sequence numbers are ignored. server `update` and
`navigation` messages carry a sequence; the renderer requests a resync when it
detects a gap or cannot apply a patch.
