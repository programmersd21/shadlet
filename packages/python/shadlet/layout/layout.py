"""Flexbox and grid layout components.

These components compile declarative Python values into CSS styles and a small
set of renderer-recognised props. No browser layout engine is reimplemented.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.layout.values import (
    Length,
    Responsive,
    css_length,
    css_number,
    css_spacing,
    grid_tracks,
    set_style,
)

HTML_TAGS = (
    "div",
    "section",
    "main",
    "header",
    "footer",
    "nav",
    "aside",
    "article",
    "ul",
    "ol",
    "li",
    "span",
)


def _align(value: str | None) -> str | None:
    if value is None:
        return None
    return {
        "start": "flex-start",
        "center": "center",
        "end": "flex-end",
        "stretch": "stretch",
        "baseline": "baseline",
    }[value]


def _justify(value: str | None) -> str | None:
    if value is None:
        return None
    return {
        "start": "flex-start",
        "center": "center",
        "end": "flex-end",
        "between": "space-between",
        "around": "space-around",
        "evenly": "space-evenly",
    }[value]


class Box(Component):
    """A styled box. Layout components below are thin, typed conveniences."""

    type = "Box"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        as_: str = "div",
        display: str | None = None,
        direction: str | None = None,
        align: str | None = None,
        justify: str | None = None,
        wrap: str | None = None,
        gap: Length | None = None,
        padding: Length | tuple[Length, ...] | None = None,
        margin: Length | tuple[Length, ...] | None = None,
        width: Length | None = None,
        height: Length | None = None,
        min_width: Length | None = None,
        max_width: Length | None = None,
        min_height: Length | None = None,
        max_height: Length | None = None,
        flex_grow: float | None = None,
        flex_shrink: float | None = None,
        overflow: str | None = None,
        position: str | None = None,
        top: Length | None = None,
        right: Length | None = None,
        bottom: Length | None = None,
        left: Length | None = None,
        z_index: int | None = None,
        class_name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> None:
        if as_ not in HTML_TAGS:
            raise ComponentError(f"as_ must be one of {', '.join(HTML_TAGS)}")
        if direction is not None:
            validate_choice(
                direction,
                ("row", "row-reverse", "column", "column-reverse"),
                argument="direction",
            )
        if wrap is not None:
            validate_choice(wrap, ("nowrap", "wrap", "wrap-reverse"), argument="wrap")
        if overflow is not None:
            validate_choice(
                overflow, ("visible", "hidden", "auto", "scroll"), argument="overflow"
            )
        if position is not None:
            validate_choice(
                position,
                ("static", "relative", "absolute", "fixed", "sticky"),
                argument="position",
            )
        if align is not None:
            validate_choice(
                align,
                ("start", "center", "end", "stretch", "baseline"),
                argument="align",
            )
        if justify is not None:
            validate_choice(
                justify,
                ("start", "center", "end", "between", "around", "evenly"),
                argument="justify",
            )

        css: dict[str, Any] = dict(style or {})
        set_style(css, "display", display)
        set_style(css, "flexDirection", direction)
        set_style(css, "alignItems", _align(align))
        set_style(css, "justifyContent", _justify(justify))
        set_style(css, "flexWrap", wrap)
        set_style(css, "gap", css_length(gap, argument="gap"))
        set_style(css, "padding", css_spacing(padding, argument="padding"))
        set_style(css, "margin", css_spacing(margin, argument="margin"))
        set_style(css, "width", css_length(width, argument="width"))
        set_style(css, "height", css_length(height, argument="height"))
        set_style(css, "minWidth", css_length(min_width, argument="min_width"))
        set_style(css, "maxWidth", css_length(max_width, argument="max_width"))
        set_style(css, "minHeight", css_length(min_height, argument="min_height"))
        set_style(css, "maxHeight", css_length(max_height, argument="max_height"))
        set_style(css, "flexGrow", css_number(flex_grow, argument="flex_grow"))
        set_style(css, "flexShrink", css_number(flex_shrink, argument="flex_shrink"))
        set_style(css, "overflow", overflow)
        set_style(css, "position", position)
        set_style(css, "top", css_length(top, argument="top"))
        set_style(css, "right", css_length(right, argument="right"))
        set_style(css, "bottom", css_length(bottom, argument="bottom"))
        set_style(css, "left", css_length(left, argument="left"))
        set_style(css, "zIndex", css_number(z_index, argument="z_index"))

        super().__init__(*children, class_name=class_name, style=css, as_=as_)


class Row(Box):
    type = "Row"

    def __init__(self, *children: Child | Sequence[Child], **kwargs: Any) -> None:
        kwargs.setdefault("display", "flex")
        kwargs.setdefault("direction", "row")
        super().__init__(*children, **kwargs)


class Column(Box):
    type = "Column"

    def __init__(self, *children: Child | Sequence[Child], **kwargs: Any) -> None:
        kwargs.setdefault("display", "flex")
        kwargs.setdefault("direction", "column")
        super().__init__(*children, **kwargs)


class Stack(Column):
    type = "Stack"

    def __init__(self, *children: Child | Sequence[Child], **kwargs: Any) -> None:
        kwargs.setdefault("gap", 8)
        super().__init__(*children, **kwargs)


class Wrap(Row):
    type = "Wrap"

    def __init__(self, *children: Child | Sequence[Child], **kwargs: Any) -> None:
        kwargs.setdefault("wrap", "wrap")
        kwargs.setdefault("gap", 8)
        super().__init__(*children, **kwargs)


class Container(Box):
    type = "Container"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        max_width: Length = 1200,
        padding: Length | tuple[Length, ...] = 24,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("display", "flex")
        kwargs.setdefault("direction", "column")
        kwargs.setdefault("width", "100%")
        kwargs.setdefault("margin", (0, "auto"))
        kwargs["max_width"] = max_width
        kwargs["padding"] = padding
        super().__init__(*children, **kwargs)


class Center(Box):
    type = "Center"

    def __init__(self, *children: Child | Sequence[Child], **kwargs: Any) -> None:
        kwargs.setdefault("display", "flex")
        kwargs.setdefault("align", "center")
        kwargs.setdefault("justify", "center")
        super().__init__(*children, **kwargs)


class Spacer(Box):
    type = "Spacer"

    def __init__(self, *, flex: float = 1, class_name: str | None = None) -> None:
        super().__init__(display="block", flex_grow=flex, class_name=class_name)


class Positioned(Box):
    type = "Positioned"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        top: Length | None = None,
        right: Length | None = None,
        bottom: Length | None = None,
        left: Length | None = None,
        z_index: int | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("position", "absolute")
        kwargs["top"] = top
        kwargs["right"] = right
        kwargs["bottom"] = bottom
        kwargs["left"] = left
        kwargs["z_index"] = z_index
        super().__init__(*children, **kwargs)


class Expanded(Box):
    type = "Expanded"

    def __init__(
        self, *children: Child | Sequence[Child], flex: float = 1, **kwargs: Any
    ) -> None:
        kwargs.setdefault("display", "flex")
        kwargs.setdefault("direction", "column")
        kwargs["flex_grow"] = flex
        super().__init__(*children, **kwargs)


class SizedBox(Box):
    type = "SizedBox"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        width: Length | None = None,
        height: Length | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs["width"] = width
        kwargs["height"] = height
        super().__init__(*children, **kwargs)


class Grid(Component):
    type = "Grid"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        columns: int | Responsive | None = None,
        rows: int | Responsive | None = None,
        gap: Length | None = None,
        column_gap: Length | None = None,
        row_gap: Length | None = None,
        align: str | None = None,
        justify: str | None = None,
        padding: Length | tuple[Length, ...] | None = None,
        width: Length | None = None,
        class_name: str | None = None,
        style: dict[str, Any] | None = None,
        as_: str = "div",
    ) -> None:
        if as_ not in HTML_TAGS:
            raise ComponentError(f"as_ must be one of {', '.join(HTML_TAGS)}")
        if align is not None:
            validate_choice(
                align,
                ("start", "center", "end", "stretch", "baseline"),
                argument="align",
            )
        if justify is not None:
            validate_choice(
                justify,
                ("start", "center", "end", "between", "around", "evenly"),
                argument="justify",
            )
        css: dict[str, Any] = dict(style or {})
        set_style(css, "gap", css_length(gap, argument="gap"))
        set_style(css, "columnGap", css_length(column_gap, argument="column_gap"))
        set_style(css, "rowGap", css_length(row_gap, argument="row_gap"))
        set_style(css, "alignItems", _align(align))
        set_style(css, "justifyContent", _justify(justify))
        set_style(css, "padding", css_spacing(padding, argument="padding"))
        set_style(css, "width", css_length(width, argument="width"))
        super().__init__(
            *children,
            class_name=class_name,
            style=css,
            as_=as_,
            columns=grid_tracks(columns, argument="columns"),
            rows=grid_tracks(rows, argument="rows"),
        )


class GridItem(Component):
    type = "GridItem"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        column_span: int = 1,
        row_span: int = 1,
        class_name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> None:
        if (
            isinstance(column_span, bool)
            or not isinstance(column_span, int)
            or column_span < 1
        ):
            raise ComponentError("column_span must be a positive integer")
        if isinstance(row_span, bool) or not isinstance(row_span, int) or row_span < 1:
            raise ComponentError("row_span must be a positive integer")
        css: dict[str, Any] = dict(style or {})
        css["gridColumn"] = f"span {column_span}"
        css["gridRow"] = f"span {row_span}"
        super().__init__(*children, class_name=class_name, style=css)


class ScrollArea(Component):
    type = "ScrollArea"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        height: Length | None = None,
        width: Length | None = None,
        orientation: str = "vertical",
        class_name: str | None = None,
    ) -> None:
        validate_choice(orientation, ("vertical", "horizontal"), argument="orientation")
        style: dict[str, Any] = {}
        set_style(style, "height", css_length(height, argument="height"))
        set_style(style, "width", css_length(width, argument="width"))
        super().__init__(
            *children,
            class_name=class_name,
            style=style,
            orientation=orientation,
        )


__all__ = [
    "Box",
    "Center",
    "Column",
    "Container",
    "Expanded",
    "Grid",
    "GridItem",
    "Positioned",
    "Responsive",
    "Row",
    "ScrollArea",
    "SizedBox",
    "Spacer",
    "Stack",
    "Wrap",
]
