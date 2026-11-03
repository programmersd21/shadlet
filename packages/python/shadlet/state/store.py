"""Per-session state storage and snapshots."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from shadlet.protocol.models import StatePatch
from shadlet.state.state import State


class StateStore:
    """Isolated state slots for a single session."""

    __slots__ = ("_states", "_values")

    def __init__(self) -> None:
        self._states: dict[str, State[Any]] = {}
        self._values: dict[str, Any] = {}

    def get(
        self,
        key: str,
        initial: Any,
        on_change: Callable[[str], None],
    ) -> State[Any]:
        existing = self._states.get(key)
        if existing is not None:
            return existing
        state: State[Any] = State(initial, key=key, on_change=on_change)
        self._states[key] = state
        self._values[key] = copy.deepcopy(state.value)
        return state

    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self._values)

    def get_existing(self, key: str) -> State[Any] | None:
        return self._states.get(key)

    def sync(self, key: str) -> None:
        state = self._states[key]
        self._values[key] = copy.deepcopy(state.value)

    def diff(self, previous: dict[str, Any]) -> list[StatePatch]:
        patches: list[StatePatch] = []
        for key, value in self._values.items():
            if key not in previous or previous[key] != value:
                patches.append(StatePatch(op="set", key=key, value=value))
        for key in previous:
            if key not in self._values:
                patches.append(StatePatch(op="delete", key=key))
        return patches


__all__ = ["StateStore"]
