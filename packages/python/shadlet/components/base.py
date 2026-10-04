"""Core component model.

Components are plain Python objects with explicit constructors. They are
converted to protocol nodes by :mod:`shadlet.runtime.render`; they never contain
serialized callbacks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, ClassVar, Union

from shadlet._json import NotSerializableError, to_wire_value
from shadlet.state.state import State

_UNSET = object()
UNSET: Any = _UNSET


class ComponentError(ValueError):
    """Raised for invalid component construction or composition."""


# Use explicit Union so mypy resolves all members with from __future__ annotations.
Child = Union["Component", str, int, float, State[Any], None]
EventHandler = Callable[..., Any]


def normalize_children(children: Sequence[Any]) -> list[Child]:
    """Flatten child sequences and reject values React cannot render."""

    from shadlet.state.state import State

    result: list[Child] = []
    for child in children:
        if child is None:
            continue
        if isinstance(child, (Component, State)):
            result.append(child)
            continue
        if isinstance(child, (str, int, float)) and not isinstance(child, bool):
            result.append(child)
            continue
        if isinstance(child, (list, tuple)):
            result.extend(normalize_children(child))
            continue
        if isinstance(child, bool):
            raise ComponentError(
                "boolean children are ambiguous; render text or conditionally include a child"
            )
        raise ComponentError(
            f"unsupported child of type {type(child).__name__}; "
            "expected a component, string, number, sequence or None"
        )
    return result


class Component:
    """Base class for all shadlet components."""

    type: ClassVar[str] = "Element"
    __slots__ = ("children", "events", "props", "slots")

    def __init__(
        self,
        *children: Child | Sequence[Child],
        key: str | None = None,
        class_name: str | None = None,
        style: Mapping[str, Any] | None = None,
        **props: Any,
    ) -> None:
        self.children = normalize_children(children)
        self.props: dict[str, Any] = {}
        self.events: dict[str, EventHandler] = {}
        self.slots: dict[str, list[Child]] = {}
        if class_name is not None:
            self.props["className"] = class_name
        if style is not None:
            self.props["style"] = to_wire_value(dict(style), path=f"{self.type}.style")
        for name, value in props.items():
            if value is not UNSET:
                self.props[name] = value
        if key is not None:
            self.props["data-shadlet-key"] = key

    def add_slot(self, name: str, value: Any) -> None:
        if not name or not name.isidentifier():
            raise ComponentError(f"invalid slot name {name!r}")
        if value is None:
            self.slots[name] = []
            return
        if isinstance(value, (list, tuple)):
            self.slots[name] = normalize_children(value)
        else:
            self.slots[name] = normalize_children([value])

    def bind(self, event: str, handler: EventHandler | None) -> None:
        if handler is None:
            return
        if not callable(handler):
            raise ComponentError(f"event {event!r} handler must be callable")
        if event in self.events:
            raise ComponentError(f"event {event!r} is already bound on {self.type}")
        self.events[event] = handler

    def __repr__(self) -> str:
        props = ", ".join(f"{key}={value!r}" for key, value in self.props.items())
        children = ", ".join(repr(child) for child in self.children)
        parts = [part for part in (props, children) if part]
        return f"{self.type}({', '.join(parts)})"


def as_component(value: Any, *, argument: str) -> Component:
    if not isinstance(value, Component):
        raise ComponentError(
            f"{argument} must be a Component, got {type(value).__name__}"
        )
    return value


def validate_choice(value: Any, choices: Sequence[Any], *, argument: str) -> Any:
    if value not in choices:
        rendered = ", ".join(repr(choice) for choice in choices)
        raise ComponentError(f"{argument} must be one of {rendered}; got {value!r}")
    return value


__all__ = [
    "UNSET",
    "Child",
    "Component",
    "ComponentError",
    "EventHandler",
    "NotSerializableError",
    "as_component",
    "normalize_children",
    "validate_choice",
]
