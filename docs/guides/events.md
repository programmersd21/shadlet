# events

events are registered with `on_*` arguments. callbacks are never serialised. shadlet assigns opaque event ids and keeps a server-side mapping.

## example

```python
def increment(event: ui.ClickEvent):
    count.value += 1


ui.Button("increment", on_click=increment)
```

## async handlers

handlers may be coroutines. exceptions are reported to the client as `handler_error`.

## ordering

events are processed in the order received. duplicate sequence numbers are ignored.
