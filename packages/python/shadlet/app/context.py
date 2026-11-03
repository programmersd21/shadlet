"""Application context passed to page functions."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from shadlet.components.enums import ToastLevel
from shadlet.protocol.models import ToastMessage
from shadlet.state.state import State

if TYPE_CHECKING:
    from shadlet.runtime.session import Session
    from shadlet.runtime.tasks import BackgroundTask

QueryT = TypeVar("QueryT")


def _query_parser(default: QueryT) -> Callable[[str], QueryT]:
    if isinstance(default, bool):

        def parse_bool(value: str) -> QueryT:
            normalised = value.lower()
            if normalised not in {"true", "false", "1", "0"}:
                raise ValueError("expected true, false, 1, or 0")
            return cast(QueryT, normalised in {"true", "1"})

        return parse_bool
    if default is None or isinstance(default, str):
        return cast(Callable[[str], QueryT], lambda value: value)
    if isinstance(default, (int, float)):
        return cast(Callable[[str], QueryT], type(default))
    raise TypeError("parse is required for custom query parameter types")


@dataclass(frozen=True, slots=True)
class RouteMatch:
    path: str
    pattern: str
    title: str
    params: dict[str, str] = field(default_factory=dict)
    not_found: bool = False
    query_params: dict[str, str] = field(default_factory=dict)


class Context:
    """Per-request context with session-isolated state and navigation."""

    __slots__ = ("_session", "params", "route")

    def __init__(self, session: Session, route: RouteMatch) -> None:
        self._session = session
        self.route = route
        self.params = route.params

    @property
    def path(self) -> str:
        return self.route.path

    def state(self, initial: Any, *, key: str | None = None) -> State[Any]:
        """Return a session-scoped reactive state slot.

        Without an explicit key the slot is keyed by the calling source
        location, so moving a line of code intentionally creates a new slot.
        """

        if key is not None:
            if not isinstance(key, str) or not key:
                raise ValueError("state key must be a non-empty string")
            full_key = f"{self.route.pattern}:{key}"
        else:
            frame = inspect.currentframe()
            caller = frame.f_back if frame is not None else None
            while caller is not None and caller.f_code.co_filename == __file__:
                caller = caller.f_back
            if caller is None:
                raise RuntimeError("could not determine state call site")
            full_key = (
                f"{self.route.pattern}:{caller.f_code.co_filename}:{caller.f_lineno}"
            )
        return self._session.state_store.get(
            full_key,
            initial,
            self._session.state_changed,
        )

    def toast(
        self,
        message: str,
        *,
        description: str | None = None,
        level: ToastLevel | str = ToastLevel.DEFAULT,
        duration: int | None = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError("toast message must be a non-empty string")
        self._session.send_toast(
            ToastMessage(
                level=str(level),  # type: ignore[arg-type]
                message=message,
                description=description,
                duration=duration,
            )
        )

    def navigate(self, path: str) -> None:
        self._session.request_navigation(path)

    def start_task(
        self,
        label: str,
        worker: Callable[[BackgroundTask], Coroutine[Any, Any, Any]],
        *,
        key: str | None = None,
    ) -> BackgroundTask:
        """Start an async task owned by this session.

        ``worker`` receives a :class:`BackgroundTask` for progress updates.
        Use ``asyncio.to_thread`` inside the worker for blocking I/O or CPU-bound
        synchronous functions.
        """
        if not isinstance(label, str) or not label.strip():
            raise ValueError("task label must be a non-empty string")
        if not callable(worker):
            raise TypeError("worker must be an async callable")
        worker_call = inspect.getattr_static(type(worker), "__call__", None)
        if not (
            inspect.iscoroutinefunction(worker)
            or inspect.iscoroutinefunction(worker_call)
        ):
            raise TypeError("worker must be an async callable")
        from shadlet.runtime.tasks import new_task_id, start_background_task

        task_id = new_task_id()
        state = self.task_state(key if key is not None else task_id, label=label)
        if state.value.get("status") == "running":
            raise RuntimeError(f"task with key {key!r} is already running")
        state.value = {
            "id": task_id,
            "label": label,
            "status": "running",
            "progress": 0,
            "message": label,
        }
        return start_background_task(
            task_id=task_id,
            state=state,
            spawn=self._session._spawn,
            worker=worker,
        )

    def task_state(self, key: str, *, label: str = "task") -> State[dict[str, Any]]:
        """Return reactive status for a task created with the same stable key."""
        if not isinstance(key, str) or not key:
            raise ValueError("task key must be a non-empty string")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("task label must be a non-empty string")
        return self.state(
            {
                "id": "",
                "label": label,
                "status": "idle",
                "progress": 0,
                "message": "",
            },
            key=f"task:{key}",
        )

    def query_state(
        self,
        name: str,
        default: QueryT,
        *,
        key: str | None = None,
        parse: Callable[[str], QueryT] | None = None,
        serialize: Callable[[QueryT], str] = str,
        history: Literal["push", "replace"] = "replace",
    ) -> State[QueryT]:
        """Bind reactive state to one URL query parameter.

        ``parse`` converts a URL value to the state type. Assignments update
        the browser URL without triggering a page navigation.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("query parameter name must be a non-empty string")
        if key is not None and (not isinstance(key, str) or not key):
            raise ValueError("query state key must be a non-empty string")
        if not isinstance(history, str) or history not in {"push", "replace"}:
            raise ValueError("history must be 'push' or 'replace'")
        if parse is not None and not callable(parse):
            raise TypeError("parse must be callable")
        if not callable(serialize):
            raise TypeError("serialize must be callable")
        parser = parse or _query_parser(default)
        raw_value = self.route.query_params.get(name)
        try:
            initial = default if raw_value is None else parser(raw_value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid value for query parameter {name!r}") from error
        state = self.state(initial, key=f"query:{key or name}")
        self._session.bind_query_state(
            state.key, name, parser, serialize, default, history
        )
        return state


__all__ = ["Context", "RouteMatch"]
