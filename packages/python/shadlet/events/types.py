"""Typed event objects delivered to Python callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class Event:
    """Base event delivered to an application callback."""

    name: str
    node_id: str
    route: str
    value: Any = None
    checked: bool | None = None
    open: bool | None = None
    values: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    event_type: ClassVar[str] = "event"

    @classmethod
    def from_payload(
        cls,
        name: str,
        node_id: str,
        route: str,
        payload: dict[str, Any],
    ) -> Event:
        event_cls: type[Event] = {
            "click": ClickEvent,
            "change": ChangeEvent,
            "input": ChangeEvent,
            "submit": SubmitEvent,
            "open_change": OpenChangeEvent,
            "select": SelectEvent,
            "value_change": SelectEvent,
        }.get(name, Event)
        return event_cls(
            name=name,
            node_id=node_id,
            route=route,
            value=payload.get("value"),
            checked=payload.get("checked"),
            open=payload.get("open"),
            values=dict(payload.get("values") or {}),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    event_type: ClassVar[str] = "click"


@dataclass(frozen=True, slots=True)
class ChangeEvent(Event):
    event_type: ClassVar[str] = "change"


@dataclass(frozen=True, slots=True)
class SubmitEvent(Event):
    event_type: ClassVar[str] = "submit"


@dataclass(frozen=True, slots=True)
class OpenChangeEvent(Event):
    event_type: ClassVar[str] = "open_change"


@dataclass(frozen=True, slots=True)
class SelectEvent(Event):
    event_type: ClassVar[str] = "select"


@dataclass(frozen=True, slots=True)
class NavigateEvent(Event):
    event_type: ClassVar[str] = "navigate"
