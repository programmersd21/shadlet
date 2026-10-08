"""Component tree serialisation."""

from __future__ import annotations

from typing import Protocol

from shadlet._json import NotSerializableError, to_wire_value
from shadlet.components.base import Component
from shadlet.events.registry import EventRegistry
from shadlet.protocol.models import Node
from shadlet.runtime.errors import RenderError
from shadlet.state.state import State


class RenderSession(Protocol):
    event_registry: EventRegistry


def _text(value: str | float, node_id: str) -> Node:
    return Node(id=node_id, type="#text", text=str(value))


def _resolve_child(value: object, node_id: str, session: RenderSession) -> Node:
    if isinstance(value, Component):
        return serialize_component(value, session, node_id)
    if isinstance(value, State):
        resolved = value.value
        if isinstance(resolved, bool) or resolved is None:
            raise RenderError(
                f"{node_id}: state used as a child must contain a string or number, "
                f"got {type(resolved).__name__}"
            )
        if isinstance(resolved, (str, int, float)):
            return _text(resolved, node_id)
        raise RenderError(
            f"{node_id}: state used as a child must contain a string or number, "
            f"got {type(resolved).__name__}; render a component instead"
        )
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return _text(value, node_id)
    raise RenderError(f"{node_id}: unsupported child value {type(value).__name__}")


def _serialize_children(
    children: list[object],
    parent_path: str,
    session: RenderSession,
) -> list[Node]:
    result: list[Node] = []
    for index, child in enumerate(children):
        result.append(_resolve_child(child, f"{parent_path}.{index}", session))
    return result


def serialize_component(
    component: Component,
    session: RenderSession,
    node_id: str = "r",
) -> Node:
    if not isinstance(component, Component):
        raise RenderError(
            f"page returned {type(component).__name__}; expected a shadlet Component"
        )

    props: dict[str, object] = {}
    for name, value in component.props.items():
        try:
            props[name] = to_wire_value(value, path=f"{node_id}.{name}")
        except NotSerializableError as error:
            raise RenderError(str(error)) from error

    events: dict[str, str] = {}
    for event_name, handler in component.events.items():
        events[event_name] = session.event_registry.register(
            node_id, event_name, handler
        )

    children = _serialize_children(list(component.children), node_id, session)
    slots = {
        name: _serialize_children(list(values), f"{node_id}@{name}", session)
        for name, values in component.slots.items()
    }

    return Node(
        id=node_id,
        type=component.type,
        props=props,  # type: ignore[arg-type]
        children=children,
        events=events,
        slots=slots,
    )


__all__ = ["RenderSession", "serialize_component"]
