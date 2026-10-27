# state

state is session-scoped. each browser user gets an isolated state store.

## creating state

```python
count = ctx.state(0, key="count")
```

without a key, the slot is keyed by the call site.

## updating

```python
count.value += 1
count.update(lambda current: current + 1)
```

mutating a container in place does not notify the runtime. assign a new value.

## isolation

state is stored per `Session`. sessions do not share state.
