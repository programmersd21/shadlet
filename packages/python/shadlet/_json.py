"""Conversion of Python values into deterministic JSON-compatible values."""

from __future__ import annotations

import dataclasses
import datetime as _dt
import enum
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class NotSerializableError(TypeError):
    """Raised when a value cannot be represented by the shadlet protocol."""


def to_wire_value(
    value: Any, *, path: str = "value", _seen: set[int] | None = None
) -> Any:
    """Convert ``value`` to a JSON-compatible value.

    Callbacks, components, arbitrary objects and cyclic containers are rejected
    with a precise path so validation errors are actionable.
    """

    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise NotSerializableError(f"{path}: non-finite floats are not supported")
        return value
    if isinstance(value, enum.Enum):
        return to_wire_value(value.value, path=path, _seen=_seen)
    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseModel):
        return to_wire_value(value.model_dump(mode="json"), path=path, _seen=_seen)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in dataclasses.fields(value):
            result[field.name] = to_wire_value(
                getattr(value, field.name), path=f"{path}.{field.name}", _seen=_seen
            )
        return result

    from shadlet.state.state import State

    if isinstance(value, State):
        return to_wire_value(value.value, path=path, _seen=_seen)

    if _seen is None:
        _seen = set()

    if isinstance(value, Mapping):
        marker = id(value)
        if marker in _seen:
            raise NotSerializableError(f"{path}: cyclic mappings are not supported")
        _seen.add(marker)
        try:
            mapping_result: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise NotSerializableError(f"{path}: mapping keys must be strings")
                mapping_result[key] = to_wire_value(
                    item, path=f"{path}.{key}", _seen=_seen
                )
            return mapping_result
        finally:
            _seen.discard(marker)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        marker = id(value)
        if marker in _seen:
            raise NotSerializableError(f"{path}: cyclic sequences are not supported")
        _seen.add(marker)
        try:
            return [
                to_wire_value(item, path=f"{path}[{index}]", _seen=_seen)
                for index, item in enumerate(value)
            ]
        finally:
            _seen.discard(marker)

    if isinstance(value, (set, frozenset)):
        raise NotSerializableError(
            f"{path}: sets are not supported because their order is not deterministic"
        )
    if callable(value):
        raise NotSerializableError(
            f"{path}: callbacks must be passed to an on_* argument, not as data"
        )

    from shadlet.components.base import Component

    if isinstance(value, Component):
        raise NotSerializableError(
            f"{path}: components cannot be used as props; use a named slot or children"
        )
    raise NotSerializableError(
        f"{path}: unsupported value of type {type(value).__name__}"
    )
