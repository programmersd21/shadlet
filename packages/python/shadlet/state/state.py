"""Session-scoped reactive state."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from shadlet._json import to_wire_value

T = TypeVar("T")


class State(Generic[T]):
    """A reactive value bound to one session and one route.

    Values are normalised to JSON-compatible Python values on assignment. This
    keeps protocol serialisation predictable and prevents callbacks or arbitrary
    objects from leaking onto the wire. Mutating a container in place does not
    notify the runtime; assign a new value instead.
    """

    __slots__ = ("_key", "_on_change", "_value")

    def __init__(
        self,
        initial: T,
        *,
        key: str,
        on_change: Callable[[str], None],
    ) -> None:
        self._key = key
        self._on_change = on_change
        self._value = to_wire_value(initial, path=f"state[{key!r}]")

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        normalised = to_wire_value(new_value, path=f"state[{self._key!r}]")
        if normalised == self._value:
            return
        self._value = normalised
        self._on_change(self._key)

    def update(self, function: Callable[[T], T]) -> None:
        """Set the state to ``function(current_value)``."""

        self.value = function(self.value)

    def __repr__(self) -> str:
        return f"State(key={self._key!r}, value={self._value!r})"


__all__ = ["State"]
