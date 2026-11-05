"""Text, headings, links and icon components."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.components.enums import TextVariant
from shadlet.components.icon_data import ICON_NAMES

TEXT_TAGS = ("p", "span", "div", "label", "strong", "em", "code", "small")


class Text(Component):
    type = "Text"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        variant: TextVariant | str = TextVariant.DEFAULT,
        as_: str = "p",
        class_name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> None:
        validate_choice(variant, tuple(TextVariant), argument="variant")
        if as_ not in TEXT_TAGS:
            raise ComponentError(f"as_ must be one of {', '.join(TEXT_TAGS)}")
        super().__init__(
            *children,
            variant=str(variant),
            as_=as_,
            class_name=class_name,
            style=style,
        )


class Heading(Component):
    type = "Heading"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        level: int = 1,
        class_name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(level, bool) or level not in (1, 2, 3, 4, 5, 6):
            raise ComponentError("level must be an integer from 1 to 6")
        super().__init__(*children, level=level, class_name=class_name, style=style)


class Link(Component):
    type = "Link"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        href: str,
        external: bool = False,
        target: str | None = None,
        rel: str | None = None,
        class_name: str | None = None,
        on_click: Any = None,
    ) -> None:
        if not isinstance(href, str) or not href:
            raise ComponentError("href must be a non-empty string")
        super().__init__(
            *children,
            href=href,
            external=external,
            target=target,
            rel=rel,
            class_name=class_name,
        )
        self.bind("click", on_click)


class Icon(Component):
    type = "Icon"

    def __init__(
        self,
        name: str,
        *,
        size: int | str = 16,
        stroke_width: float = 2,
        color: str | None = None,
        label: str | None = None,
        class_name: str | None = None,
    ) -> None:
        if name not in ICON_NAMES:
            raise ComponentError(
                f"unknown icon {name!r}; discover names with shadlet.ICON_NAMES "
                "or shadlet.icons"
            )
        if isinstance(size, bool) or not isinstance(size, (int, float, str)):
            raise ComponentError("size must be a number or CSS length string")
        if isinstance(stroke_width, bool) or not isinstance(stroke_width, (int, float)):
            raise ComponentError("stroke_width must be a number")
        super().__init__(
            name=name,
            size=size,
            strokeWidth=stroke_width,
            color=color,
            label=label,
            class_name=class_name,
        )


class Code(Text):
    type = "Code"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            *children, variant=TextVariant.CODE, as_="code", class_name=class_name
        )


class Kbd(Component):
    type = "Kbd"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        class_name: str | None = None,
    ) -> None:
        super().__init__(*children, class_name=class_name)


__all__ = ["ICON_NAMES", "Code", "Heading", "Icon", "Kbd", "Link", "Text"]
