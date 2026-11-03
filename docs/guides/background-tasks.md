# background tasks

use `Context.start_task` to schedule an async worker owned by the active
session. use `Context.task_state` with the same stable key to render the
worker's progress.

```python
import asyncio
import shadlet as ui

app = ui.App("task progress")


@app.page("/")
def home(ctx: ui.Context):
    task_state = ctx.task_state("report", label="report")

    async def process(task: ui.BackgroundTask):
        for index in range(10):
            await asyncio.sleep(0.1)
            await task.update(progress=(index + 1) * 10, message="processing")

    async def start(event: ui.ClickEvent):
        ctx.start_task("report", process, key="report")

    return ui.Column(
        ui.Text(task_state.value["message"]),
        ui.Progress(value=task_state.value["progress"]),
        ui.Button("start", on_click=start),
    )
```

workers must be async callables. blocking operations should be moved to
`asyncio.to_thread`; do not call synchronous blocking functions on the event
loop. update progress with integers from 0 to 100. a task handle can also be
cancelled with `await task.cancel()`.

task state is reactive and belongs to the session. reconnecting restores the
session while it remains alive. disconnect alone does not cancel a worker;
session expiry and application shutdown cancel session-owned tasks. task
execution and state are in memory and process-local, so this is not a
multi-worker job queue. failed workers are logged and expose a generic `failed`
status instead of an exception message.
