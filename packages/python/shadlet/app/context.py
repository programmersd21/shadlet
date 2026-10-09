"""Application context passed to page functions."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from shadlet.components.enums import ToastLevel
from shadlet.protocol.models import ToastMessage
from shadlet.state.state import State

if TYPE_CHECKING:
    from shadlet.runtime.session import Session


@dataclass(frozen=True, slots=True)
class RouteMatch:
    path: str
    pattern: str
    title: str
    params: dict[str, str] = field(default_factory=dict)
    not_found: bool = False


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


__all__ = ["Context", "RouteMatch"]
