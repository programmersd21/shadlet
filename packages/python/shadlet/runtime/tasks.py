"""Session-owned background task state."""

from __future__ import annotations

import asyncio
import inspect
import logging
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from shadlet.state.state import State

logger = logging.getLogger("shadlet.tasks")


class BackgroundTask:
    """A session-scoped task with JSON-serializable reactive progress state."""

    __slots__ = ("_state", "_task", "id")

    def __init__(
        self,
        task_id: str,
        state: State[dict[str, Any]],
    ) -> None:
        self.id = task_id
        self._state = state
        self._task: asyncio.Task[Any] | None = None

    @property
    def state(self) -> State[dict[str, Any]]:
        """Return reactive task status for rendering in the application."""
        return self._state

    @property
    def done(self) -> bool:
        return self._task is not None and self._task.done()

    async def update(self, *, progress: int, message: str | None = None) -> None:
        """Update progress from 0 to 100 and an optional status message."""
        if isinstance(progress, bool) or not isinstance(progress, int):
            raise TypeError("progress must be an integer")
        if not 0 <= progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        if message is not None and not isinstance(message, str):
            raise TypeError("message must be a string or None")
        current = dict(self._state.value)
        if current["status"] != "running":
            raise RuntimeError("only a running task can be updated")
        current.update(progress=progress, message=message or current["message"])
        self._state.value = current

    async def complete(self, *, message: str = "completed") -> None:
        """Mark this task as successfully completed."""
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string")
        current = dict(self._state.value)
        if current["status"] != "running":
            return
        current.update(status="completed", progress=100, message=message)
        self._state.value = current

    async def cancel(self) -> None:
        """Cancel the worker and mark its state as cancelled."""
        task = self._task
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        current = dict(self._state.value)
        if current["status"] == "running":
            current.update(status="cancelled", message="cancelled")
            self._state.value = current


def start_background_task(
    *,
    task_id: str,
    state: State[dict[str, Any]],
    spawn: Callable[[Coroutine[Any, Any, Any]], asyncio.Task[Any]],
    worker: Callable[[BackgroundTask], Coroutine[Any, Any, Any]],
) -> BackgroundTask:
    """Create and schedule a worker, isolating errors to this task."""
    task = BackgroundTask(task_id, state)

    async def run() -> None:
        try:
            result = worker(task)
            if inspect.isawaitable(result):
                await result
            await task.complete()
        except asyncio.CancelledError:
            current = dict(state.value)
            if current["status"] == "running":
                current.update(status="cancelled", message="cancelled")
                state.value = current
            raise
        except Exception:
            logger.exception("background task %s failed", task_id)
            current = dict(state.value)
            current.update(status="failed", message="task failed")
            state.value = current

    task._task = spawn(run())
    return task


def new_task_id() -> str:
    """Return a unique opaque task identifier."""
    return uuid.uuid4().hex


__all__ = ["BackgroundTask", "new_task_id", "start_background_task"]
