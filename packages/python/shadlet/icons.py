"""Generated Lucide icon names and a convenient namespace API."""

from __future__ import annotations

from typing import Any

from shadlet.components.icon_data import ICON_NAMES, LUCIDE_VERSION


class _IconNamespace:
    """Expose every Lucide name as ``icons.arrow_up_right(...)``."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Any:
        icon_name = name.replace("_", "-")
        if icon_name not in ICON_NAMES:
            raise AttributeError(f"unknown icon {name!r}")
        from shadlet.components.typography import Icon

        def icon(**kwargs: Any) -> Icon:
            return Icon(icon_name, **kwargs)

        icon.__name__ = name
        icon.__qualname__ = f"icons.{name}"
        return icon

    def __dir__(self) -> list[str]:
        return sorted(name.replace("-", "_") for name in ICON_NAMES)


icons = _IconNamespace()

__all__ = ["ICON_NAMES", "LUCIDE_VERSION", "icons"]
