"""Safe mapping between opaque event ids and Python callbacks."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from shadlet.components.base import EventHandler


@dataclass(frozen=True, slots=True)
class EventBinding:
    event_id: str
    node_path: str
    event_name: str
    handler: EventHandler


class EventRegistry:
    """Per-render event id registry.

    Identifiers are deterministic for a node path and event name so that
    unchanged components keep stable ids across renders. Callbacks live only in
    this server-side registry and are never serialized.
    """

    __slots__ = ("_bindings",)

    def __init__(self) -> None:
        self._bindings: dict[str, EventBinding] = {}

    def reset(self) -> None:
        self._bindings.clear()

    def register(self, node_path: str, event_name: str, handler: EventHandler) -> str:
        digest = hashlib.blake2s(
            f"{node_path}:{event_name}".encode(), digest_size=8
        ).hexdigest()
        event_id = f"evt_{digest}"
        self._bindings[event_id] = EventBinding(
            event_id=event_id,
            node_path=node_path,
            event_name=event_name,
            handler=handler,
        )
        return event_id

    def resolve(self, event_id: str) -> EventBinding | None:
        return self._bindings.get(event_id)

    def __len__(self) -> int:
        return len(self._bindings)

    def snapshot_ids(self) -> dict[str, Any]:
        return {
            event_id: {"node": binding.node_path, "event": binding.event_name}
            for event_id, binding in self._bindings.items()
        }


__all__ = ["EventBinding", "EventRegistry"]
