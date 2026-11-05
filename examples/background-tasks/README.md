# Background work

```console
cd examples/background-tasks
python main.py
```

Start an async report job and watch per-session progress update. The example
uses a short sleep in place of real I/O. Use `asyncio.to_thread` for blocking
work; Shadlet background tasks are in-memory and process-local, not a durable
job queue.
