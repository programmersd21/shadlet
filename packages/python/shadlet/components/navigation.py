"""Tabs, breadcrumbs, pagination and sidebar navigation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.components.enums import Orientation
from shadlet.components.options import (
    BreadcrumbItem,
    SidebarItem,
    SidebarSection,
    TabItem,
)


def normalize_tabs(
    items: Sequence[TabItem | Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[Any]]:
    result: list[dict[str, Any]] = []
    contents: list[Any] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if isinstance(item, TabItem):
            value, label, content = item.value, item.label, item.content
            disabled, icon = item.disabled, item.icon
        elif isinstance(item, Mapping):
            value = str(item.get("value", ""))
            label = str(item.get("label", value))
            content = item.get("content")
            disabled = bool(item.get("disabled", False))
            icon = item.get("icon")
        else:
            raise ComponentError(f"tab {index} must be TabItem or mapping")
        if not value or not label:
            raise ComponentError(f"tab {index} requires value and label")
        if value in seen:
            raise ComponentError(f"duplicate tab value {value!r}")
        seen.add(value)
        result.append(
            {
                "value": value,
                "label": label,
                "panel": f"panel_{index}",
                "disabled": disabled,
                "icon": icon,
            }
        )
        contents.append(content)
    return result, contents


class Tabs(Component):
    type = "Tabs"

    def __init__(
        self,
        items: Sequence[TabItem | Mapping[str, Any]],
        *,
        value: Any = None,
        default_value: str | None = None,
        orientation: Orientation | str = Orientation.HORIZONTAL,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        normalized, contents = normalize_tabs(items)
        if default_value is None and normalized:
            default_value = normalized[0]["value"]
        super().__init__(
            items=normalized,
            value=value,
            defaultValue=default_value,
            orientation=str(orientation),
            class_name=class_name,
        )
        for index, content in enumerate(contents):
            self.add_slot(f"panel_{index}", content)
        self.bind("value_change", on_change)


class Breadcrumb(Component):
    type = "Breadcrumb"

    def __init__(
        self,
        items: Sequence[BreadcrumbItem | Mapping[str, Any]],
        *,
        separator: str = "/",
        class_name: str | None = None,
        on_click: Any = None,
    ) -> None:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if isinstance(item, BreadcrumbItem):
                label, href = item.label, item.href
            elif isinstance(item, Mapping):
                label = str(item.get("label", ""))
                href = item.get("href")
            else:
                raise ComponentError(
                    f"breadcrumb item {index} must be BreadcrumbItem or mapping"
                )
            if not label:
                raise ComponentError(f"breadcrumb item {index} requires a label")
            normalized.append({"label": label, "href": href})
        if not normalized:
            raise ComponentError("Breadcrumb requires at least one item")
        super().__init__(items=normalized, separator=separator, class_name=class_name)
        self.bind("click", on_click)


class Pagination(Component):
    type = "Pagination"

    def __init__(
        self,
        *,
        page: Any = 1,
        total_pages: Any,
        sibling_count: int = 1,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        if (
            isinstance(sibling_count, bool)
            or not isinstance(sibling_count, int)
            or sibling_count < 0
        ):
            raise ComponentError("sibling_count must be a non-negative integer")
        if isinstance(total_pages, int) and total_pages < 1:
            raise ComponentError("total_pages must be at least 1")
        if isinstance(page, int) and not isinstance(page, bool) and page < 1:
            raise ComponentError("page must be at least 1")
        super().__init__(
            page=page,
            totalPages=total_pages,
            siblingCount=sibling_count,
            class_name=class_name,
        )
        self.bind("change", on_change)


def _sidebar_item(
    item: SidebarItem | Mapping[str, Any] | str, *, index: int
) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "label": item,
            "href": None,
            "icon": None,
            "active": False,
            "badge": None,
        }
    if isinstance(item, SidebarItem):
        return {
            "label": item.label,
            "href": item.href,
            "icon": item.icon,
            "active": item.active,
            "badge": item.badge,
        }
    if isinstance(item, Mapping):
        label = str(item.get("label", ""))
        if not label:
            raise ComponentError(f"sidebar item {index} requires a label")
        return {
            "label": label,
            "href": item.get("href"),
            "icon": item.get("icon"),
            "active": bool(item.get("active", False)),
            "badge": item.get("badge"),
        }
    raise ComponentError(
        f"sidebar item {index} must be a string, SidebarItem or mapping"
    )


def normalize_sidebar_sections(
    sections: Sequence[SidebarSection | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for section_index, section in enumerate(sections):
        if isinstance(section, SidebarSection):
            label = section.label
            items = section.items
        elif isinstance(section, Mapping):
            label = section.get("label")
            items = section.get("items", ())
        else:
            raise ComponentError(
                f"sidebar section {section_index} must be SidebarSection or mapping"
            )
        result.append(
            {
                "label": str(label) if label is not None else None,
                "items": [
                    _sidebar_item(item, index=item_index)
                    for item_index, item in enumerate(items)
                ],
            }
        )
    return result


class Sidebar(Component):
    type = "Sidebar"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        sections: Sequence[SidebarSection | Mapping[str, Any]] = (),
        header: Child | Sequence[Child] | None = None,
        footer: Child | Sequence[Child] | None = None,
        collapsible: str = "icon",
        side: str = "left",
        default_open: bool = True,
        class_name: str | None = None,
    ) -> None:
        validate_choice(
            collapsible, ("offcanvas", "icon", "none"), argument="collapsible"
        )
        validate_choice(side, ("left", "right"), argument="side")
        super().__init__(
            *children,
            sections=normalize_sidebar_sections(sections),
            collapsible=collapsible,
            side=side,
            defaultOpen=default_open,
            class_name=class_name,
        )
        self.add_slot("header", header)
        self.add_slot("footer", footer)


class ThemeToggle(Component):
    type = "ThemeToggle"

    def __init__(self, *, class_name: str | None = None) -> None:
        super().__init__(class_name=class_name)


__all__ = [
    "Breadcrumb",
    "Pagination",
    "Sidebar",
    "Tabs",
    "ThemeToggle",
    "normalize_sidebar_sections",
    "normalize_tabs",
]
