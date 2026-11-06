"""Dialogs, menus, popovers, tooltips and command surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.components.enums import Direction, SelectAlign, Side, ToastLevel
from shadlet.components.options import MenuGroup, MenuItem, NavigationItem


def _menu_item(
    item: MenuItem | Mapping[str, Any] | str, *, index: int
) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "label": item,
            "value": item,
            "icon": None,
            "shortcut": None,
            "disabled": False,
            "destructive": False,
            "separatorBefore": False,
        }
    if isinstance(item, MenuItem):
        data = {
            "label": item.label,
            "value": item.value,
            "icon": item.icon,
            "shortcut": item.shortcut,
            "disabled": item.disabled,
            "destructive": item.destructive,
            "separatorBefore": item.separator_before,
        }
    elif isinstance(item, Mapping):
        if "label" not in item:
            raise ComponentError(f"menu item {index} requires a label")
        value = item.get("value", item["label"])
        data = {
            "label": str(item["label"]),
            "value": str(value),
            "icon": item.get("icon"),
            "shortcut": item.get("shortcut"),
            "disabled": bool(item.get("disabled", False)),
            "destructive": bool(item.get("destructive", False)),
            "separatorBefore": bool(item.get("separator_before", False)),
        }
    else:
        raise ComponentError(f"menu item {index} must be a string, MenuItem or mapping")
    if not data["label"]:
        raise ComponentError(f"menu item {index} requires a non-empty label")
    if not data["value"]:
        raise ComponentError(f"menu item {index} requires a non-empty value")
    return data


def normalize_menu_items(
    items: Sequence[MenuItem | MenuGroup | Mapping[str, Any] | str],
) -> list[dict[str, Any]]:
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ComponentError("items must be a sequence")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if isinstance(item, MenuGroup):
            group_items = [_menu_item(child, index=index) for child in item.items]
            for child in group_items:
                if child["value"] in seen:
                    raise ComponentError(f"duplicate menu value {child['value']!r}")
                seen.add(child["value"])
            result.append({"kind": "group", "label": item.label, "items": group_items})
        else:
            data = _menu_item(item, index=index)
            if data["value"] in seen:
                raise ComponentError(f"duplicate menu value {data['value']!r}")
            seen.add(data["value"])
            result.append({"kind": "item", **data})
    return result


def normalize_navigation(
    items: Sequence[NavigationItem | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if isinstance(item, NavigationItem):
            label, href, children = item.label, item.href, item.children
        elif isinstance(item, Mapping):
            label = str(item.get("label", ""))
            href = item.get("href")
            children = item.get("children", ())
        else:
            raise ComponentError(
                f"navigation item {index} must be NavigationItem or mapping"
            )
        if not label:
            raise ComponentError(f"navigation item {index} requires a label")
        result.append(
            {
                "label": label,
                "href": href,
                "children": normalize_navigation(children),
            }
        )
    return result


class Dialog(Component):
    type = "Dialog"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        title: str | None = None,
        description: str | None = None,
        footer: Child | Sequence[Child] | None = None,
        open: Any = None,
        show_close: bool = True,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        super().__init__(
            *children,
            title=title,
            description=description,
            open=open,
            showClose=show_close,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.add_slot("footer", footer)
        self.bind("open_change", on_open_change)


class AlertDialog(Component):
    type = "AlertDialog"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        title: str | None = None,
        description: str | None = None,
        action: Child | Sequence[Child] | None = None,
        cancel: Child | Sequence[Child] | None = None,
        open: Any = None,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        super().__init__(
            *children,
            title=title,
            description=description,
            open=open,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.add_slot("action", action)
        self.add_slot("cancel", cancel)
        self.bind("open_change", on_open_change)


class Sheet(Component):
    type = "Sheet"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        title: str | None = None,
        description: str | None = None,
        footer: Child | Sequence[Child] | None = None,
        side: Side | str = Side.RIGHT,
        open: Any = None,
        show_close: bool = True,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        validate_choice(side, tuple(Side), argument="side")
        super().__init__(
            *children,
            title=title,
            description=description,
            side=str(side),
            open=open,
            showClose=show_close,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.add_slot("footer", footer)
        self.bind("open_change", on_open_change)


class Drawer(Component):
    type = "Drawer"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        title: str | None = None,
        description: str | None = None,
        footer: Child | Sequence[Child] | None = None,
        direction: str = "bottom",
        open: Any = None,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        validate_choice(
            direction, ("top", "right", "bottom", "left"), argument="direction"
        )
        super().__init__(
            *children,
            title=title,
            description=description,
            direction=direction,
            open=open,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.add_slot("footer", footer)
        self.bind("open_change", on_open_change)


class Popover(Component):
    type = "Popover"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        open: Any = None,
        align: SelectAlign | str = SelectAlign.CENTER,
        side: Side | str = Side.BOTTOM,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        validate_choice(align, tuple(SelectAlign), argument="align")
        validate_choice(side, tuple(Side), argument="side")
        super().__init__(
            *children,
            open=open,
            align=str(align),
            side=str(side),
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.bind("open_change", on_open_change)


class Tooltip(Component):
    type = "Tooltip"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        delay: int = 300,
        side: Side | str = Side.TOP,
        class_name: str | None = None,
    ) -> None:
        validate_choice(side, tuple(Side), argument="side")
        if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0:
            raise ComponentError("delay must be a non-negative integer")
        super().__init__(*children, delay=delay, side=str(side), class_name=class_name)
        self.add_slot("trigger", trigger)


class HoverCard(Component):
    type = "HoverCard"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        open_delay: int = 200,
        close_delay: int = 100,
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            *children,
            openDelay=open_delay,
            closeDelay=close_delay,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)


class DropdownMenu(Component):
    type = "DropdownMenu"

    def __init__(
        self,
        items: Sequence[MenuItem | MenuGroup | Mapping[str, Any] | str],
        *,
        trigger: Component,
        align: SelectAlign | str = SelectAlign.START,
        side: Side | str = Side.BOTTOM,
        label: str | None = None,
        open: Any = None,
        class_name: str | None = None,
        on_select: Any = None,
        on_open_change: Any = None,
    ) -> None:
        validate_choice(align, tuple(SelectAlign), argument="align")
        validate_choice(side, tuple(Side), argument="side")
        if not isinstance(trigger, Component):
            raise ComponentError("DropdownMenu trigger must be a Component")
        super().__init__(
            items=normalize_menu_items(items),
            align=str(align),
            side=str(side),
            label=label,
            open=open,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.bind("select", on_select)
        self.bind("open_change", on_open_change)


class ContextMenu(Component):
    type = "ContextMenu"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        items: Sequence[MenuItem | MenuGroup | Mapping[str, Any] | str],
        on_select: Any = None,
    ) -> None:
        super().__init__(*children, items=normalize_menu_items(items))
        self.bind("select", on_select)


class Menubar(Component):
    type = "Menubar"

    def __init__(
        self,
        menus: Sequence[Mapping[str, Any]],
        *,
        on_select: Any = None,
        class_name: str | None = None,
    ) -> None:
        normalized: list[dict[str, Any]] = []
        for index, menu in enumerate(menus):
            if not isinstance(menu, Mapping) or "label" not in menu:
                raise ComponentError(f"menubar menu {index} requires a label and items")
            normalized.append(
                {
                    "label": str(menu["label"]),
                    "items": normalize_menu_items(menu.get("items", ())),
                }
            )
        super().__init__(menus=normalized, class_name=class_name)
        self.bind("select", on_select)


class NavigationMenu(Component):
    type = "NavigationMenu"

    def __init__(
        self,
        items: Sequence[NavigationItem | Mapping[str, Any]],
        *,
        class_name: str | None = None,
    ) -> None:
        super().__init__(items=normalize_navigation(items), class_name=class_name)


class Command(Component):
    type = "Command"

    def __init__(
        self,
        *,
        items: Sequence[MenuItem | Mapping[str, Any] | str],
        placeholder: str = "type a command or search...",
        empty_text: str = "no results found",
        trigger: Component | None = None,
        title: str = "command palette",
        description: str | None = None,
        open: Any = None,
        class_name: str | None = None,
        on_select: Any = None,
        on_open_change: Any = None,
    ) -> None:
        super().__init__(
            items=normalize_menu_items(items),
            placeholder=placeholder,
            emptyText=empty_text,
            title=title,
            description=description,
            open=open,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.bind("select", on_select)
        self.bind("open_change", on_open_change)


class DirectionProvider(Component):
    type = "Direction"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        direction: Direction | str = Direction.LTR,
        class_name: str | None = None,
    ) -> None:
        validate_choice(direction, tuple(Direction), argument="direction")
        super().__init__(*children, dir=str(direction), class_name=class_name)


class Toast(Component):
    type = "Toast"

    def __init__(
        self,
        *,
        title: str,
        description: str | None = None,
        level: ToastLevel | str = ToastLevel.DEFAULT,
        duration: int | None = None,
        position: str | None = None,
        close_button: bool = False,
        class_name: str | None = None,
        on_dismiss: Any = None,
    ) -> None:
        if not title:
            raise ComponentError("title must be a non-empty string")
        validate_choice(level, tuple(ToastLevel), argument="level")
        if duration is not None and (
            isinstance(duration, bool) or not isinstance(duration, int) or duration < 0
        ):
            raise ComponentError("duration must be a non-negative integer")
        super().__init__(
            title=title,
            description=description,
            level=str(level),
            duration=duration,
            position=position,
            closeButton=close_button,
            class_name=class_name,
        )
        self.bind("dismiss", on_dismiss)


__all__ = [
    "AlertDialog",
    "Command",
    "ContextMenu",
    "Dialog",
    "DirectionProvider",
    "Drawer",
    "DropdownMenu",
    "HoverCard",
    "Menubar",
    "NavigationMenu",
    "Popover",
    "Sheet",
    "Tooltip",
    "normalize_menu_items",
    "normalize_navigation",
]
