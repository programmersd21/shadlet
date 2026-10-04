"""Structured option values shared by data-driven components."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SelectOption:
    value: str
    label: str
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class MenuItem:
    label: str
    value: str
    icon: str | None = None
    shortcut: str | None = None
    disabled: bool = False
    destructive: bool = False
    separator_before: bool = False


@dataclass(frozen=True, slots=True)
class MenuGroup:
    label: str
    items: tuple[MenuItem, ...]


@dataclass(frozen=True, slots=True)
class TabItem:
    value: str
    label: str
    content: Any = None
    disabled: bool = False
    icon: str | None = None


@dataclass(frozen=True, slots=True)
class AccordionItem:
    value: str
    title: str
    content: Any = None
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class BreadcrumbItem:
    label: str
    href: str | None = None


@dataclass(frozen=True, slots=True)
class TableColumn:
    key: str
    header: str
    align: str = "left"
    width: str | None = None
    sortable: bool = False
    filterable: bool = False


@dataclass(frozen=True, slots=True)
class ChartSeries:
    key: str
    label: str
    color: str | None = None


@dataclass(frozen=True, slots=True)
class SidebarItem:
    label: str
    href: str | None = None
    icon: str | None = None
    active: bool = False
    badge: str | None = None


@dataclass(frozen=True, slots=True)
class SidebarSection:
    label: str | None
    items: Sequence[SidebarItem] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    href: str | None = None
    children: tuple[NavigationItem, ...] = field(default_factory=tuple)


__all__ = [
    "AccordionItem",
    "BreadcrumbItem",
    "ChartSeries",
    "MenuGroup",
    "MenuItem",
    "NavigationItem",
    "SelectOption",
    "SidebarItem",
    "SidebarSection",
    "TabItem",
    "TableColumn",
]
