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
        return _serialize_component(value, session, node_id)
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


def _enforce_tree_limits(
    component: Component,
    *,
    max_nodes: int | None,
    max_depth: int | None,
) -> None:
    if max_nodes is None and max_depth is None:
        return
    count = 0

    def check(depth: int) -> None:
        nonlocal count
        count += 1
        if max_nodes is not None and count > max_nodes:
            raise RenderError(f"component tree exceeds {max_nodes} nodes")
        if max_depth is not None and depth > max_depth:
            raise RenderError(f"component tree exceeds depth {max_depth}")

    def visit(item: Component, depth: int) -> None:
        check(depth)
        for child in item.children:
            if isinstance(child, Component):
                visit(child, depth + 1)
            else:
                check(depth + 1)
        for values in item.slots.values():
            for child in values:
                if isinstance(child, Component):
                    visit(child, depth + 1)
                else:
                    check(depth + 1)

    visit(component, 0)


def serialize_component(
    component: Component,
    session: RenderSession,
    node_id: str = "r",
    *,
    max_nodes: int | None = None,
    max_depth: int | None = None,
) -> Node:
    if not isinstance(component, Component):
        raise RenderError(
            f"page returned {type(component).__name__}; expected a shadlet Component"
        )
    _enforce_tree_limits(component, max_nodes=max_nodes, max_depth=max_depth)
    return _serialize_component(component, session, node_id)


def _serialize_component(
    component: Component,
    session: RenderSession,
    node_id: str,
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
