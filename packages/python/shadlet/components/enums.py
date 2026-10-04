"""Finite public choices used by the component API."""

from __future__ import annotations

from enum import StrEnum


class ButtonVariant(StrEnum):
    DEFAULT = "default"
    OUTLINE = "outline"
    SECONDARY = "secondary"
    GHOST = "ghost"
    DESTRUCTIVE = "destructive"
    LINK = "link"


class ButtonSize(StrEnum):
    DEFAULT = "default"
    XS = "xs"
    SM = "sm"
    LG = "lg"
    ICON = "icon"
    ICON_XS = "icon-xs"
    ICON_SM = "icon-sm"
    ICON_LG = "icon-lg"


class ToggleVariant(StrEnum):
    DEFAULT = "default"
    OUTLINE = "outline"


class ToggleSize(StrEnum):
    DEFAULT = "default"
    SM = "sm"
    LG = "lg"


class BadgeVariant(StrEnum):
    DEFAULT = "default"
    SECONDARY = "secondary"
    DESTRUCTIVE = "destructive"
    OUTLINE = "outline"


class AlertVariant(StrEnum):
    DEFAULT = "default"
    DESTRUCTIVE = "destructive"


class TextVariant(StrEnum):
    DEFAULT = "default"
    MUTED = "muted"
    SMALL = "small"
    LEAD = "lead"
    LARGE = "large"
    BOLD = "bold"
    CODE = "code"


class HeadingLevel(StrEnum):
    H1 = "1"
    H2 = "2"
    H3 = "3"
    H4 = "4"
    H5 = "5"
    H6 = "6"


class Align(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"
    BASELINE = "baseline"


class Justify(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"
    BETWEEN = "between"
    AROUND = "around"
    EVENLY = "evenly"


class WrapMode(StrEnum):
    NOWRAP = "nowrap"
    WRAP = "wrap"
    WRAP_REVERSE = "wrap-reverse"


class Overflow(StrEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    AUTO = "auto"
    SCROLL = "scroll"


class Position(StrEnum):
    STATIC = "static"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    FIXED = "fixed"
    STICKY = "sticky"


class Side(StrEnum):
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


class Orientation(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Direction(StrEnum):
    LTR = "ltr"
    RTL = "rtl"


class Theme(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ChartKind(StrEnum):
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    RADAR = "radar"


class ToastLevel(StrEnum):
    DEFAULT = "default"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CalendarMode(StrEnum):
    SINGLE = "single"
    RANGE = "range"


class SelectAlign(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"


__all__ = [
    "AlertVariant",
    "Align",
    "BadgeVariant",
    "ButtonSize",
    "ButtonVariant",
    "CalendarMode",
    "ChartKind",
    "Direction",
    "HeadingLevel",
    "Justify",
    "Orientation",
    "Overflow",
    "Position",
    "SelectAlign",
    "Side",
    "TextVariant",
    "Theme",
    "ToastLevel",
    "ToggleSize",
    "ToggleVariant",
    "WrapMode",
]
