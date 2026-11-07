"""Application theme configuration, including typography tokens."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from shadlet.fonts import FontManager


class ThemeManager:
    """Mutable theme settings for an application.

    ``str(theme_manager)`` remains the selected mode so existing application
    code and protocol fields continue to work.
    """

    __slots__ = (
        "_fonts",
        "_mode",
        "color_tokens",
        "font_family",
        "font_sizes",
        "font_weights",
        "heading_font",
        "letter_spacing",
        "line_heights",
        "mono_font_family",
        "preset",
        "text_variants",
        "ui_font",
    )

    def __init__(
        self, mode: str = "light", *, fonts: FontManager | None = None
    ) -> None:
        if mode not in {"light", "dark", "system"}:
            raise ValueError("theme mode must be 'light', 'dark' or 'system'")
        self._mode = mode
        self._fonts = fonts if fonts is not None else FontManager()
        self.font_family: str | None = "Geist"
        self.heading_font: str | None = None
        self.ui_font: str | None = None
        self.mono_font_family: str | None = "Geist Mono"
        self.font_sizes: dict[str, Any] = {}
        self.font_weights: dict[str, Any] = {}
        self.line_heights: dict[str, Any] = {}
        self.letter_spacing: dict[str, Any] = {}
        self.text_variants: dict[str, Any] = {}
        self.color_tokens: dict[str, str] = {}
        self.preset: str | None = None

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in {"light", "dark", "system"}:
            raise ValueError("theme mode must be 'light', 'dark' or 'system'")
        self._mode = value

    def configure(self, **kwargs: Any) -> None:
        if "theme" in kwargs:
            self.mode = kwargs.pop("theme")
        if "mode" in kwargs:
            self.mode = kwargs.pop("mode")
        if "font_family" in kwargs:
            self.font_family = _optional_name(kwargs.pop("font_family"), "font_family")
        if "heading_font" in kwargs:
            self.heading_font = _optional_name(
                kwargs.pop("heading_font"), "heading_font"
            )
        if "heading_font_family" in kwargs:
            self.heading_font = _optional_name(
                kwargs.pop("heading_font_family"), "heading_font_family"
            )
        if "ui_font" in kwargs:
            self.ui_font = _optional_name(kwargs.pop("ui_font"), "ui_font")
        if "ui_font_family" in kwargs:
            self.ui_font = _optional_name(
                kwargs.pop("ui_font_family"), "ui_font_family"
            )
        if "mono_font" in kwargs:
            self.mono_font_family = _optional_name(kwargs.pop("mono_font"), "mono_font")
        if "mono_font_family" in kwargs:
            self.mono_font_family = _optional_name(
                kwargs.pop("mono_font_family"), "mono_font_family"
            )
        if "monospace_font" in kwargs:
            self.mono_font_family = _optional_name(
                kwargs.pop("monospace_font"), "monospace_font"
            )
        if "monospace_font_family" in kwargs:
            self.mono_font_family = _optional_name(
                kwargs.pop("monospace_font_family"), "monospace_font_family"
            )
        for name in (
            "font_sizes",
            "font_weights",
            "line_heights",
            "letter_spacing",
            "text_variants",
        ):
            if name in kwargs:
                value = kwargs.pop(name)
                if not isinstance(value, Mapping):
                    raise ValueError(f"{name} must be a mapping")
                getattr(self, name).update(value)
        if "tokens" in kwargs:
            tokens = kwargs.pop("tokens")
            if not isinstance(tokens, Mapping):
                raise ValueError("tokens must be a mapping")
            for key, value in tokens.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError("tokens must contain string keys and values")
                self.color_tokens[str(key)] = str(value)
        if "color_tokens" in kwargs:
            tokens = kwargs.pop("color_tokens")
            if not isinstance(tokens, Mapping):
                raise ValueError("color_tokens must be a mapping")
            for key, value in tokens.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError("color_tokens must contain string keys and values")
                self.color_tokens[str(key)] = str(value)
        if "preset" in kwargs:
            preset = kwargs.pop("preset")
            if not isinstance(preset, str) or not preset.strip():
                raise ValueError("preset must be a non-empty string")
            self.preset = preset.strip()
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise ValueError(f"unknown theme configuration options: {unknown}")

    def css_variables(self) -> dict[str, str]:
        variables: dict[str, str] = {}
        body_stack = self._fonts.font_stack(self.font_family, generic="sans-serif")
        if body_stack:
            variables["--font-sans"] = body_stack
        heading_stack = self._fonts.font_stack(
            self.heading_font or self.font_family, generic="sans-serif"
        )
        if heading_stack:
            variables["--font-heading"] = heading_stack
        ui_stack = self._fonts.font_stack(
            self.ui_font or self.font_family, generic="sans-serif"
        )
        if ui_stack:
            variables["--font-ui"] = ui_stack
        mono_stack = self._fonts.font_stack(self.mono_font_family, generic="monospace")
        if mono_stack:
            variables["--font-mono"] = mono_stack
        variables.update(self.color_tokens)
        return variables

    def css(self) -> str:
        variables = self.css_variables()
        if not variables:
            return self._fonts.css()
        body = "\n".join(f"  {key}: {value};" for key, value in variables.items())
        return f"{self._fonts.css()}\n\n:root {{\n{body}\n}}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self._mode,
            "fontFamily": self.font_family,
            "headingFont": self.heading_font,
            "uiFont": self.ui_font,
            "monoFontFamily": self.mono_font_family,
            "fontSizes": dict(self.font_sizes),
            "fontWeights": dict(self.font_weights),
            "lineHeights": dict(self.line_heights),
            "letterSpacing": dict(self.letter_spacing),
            "textVariants": dict(self.text_variants),
            "colorTokens": dict(self.color_tokens),
            "preset": self.preset,
            "variables": self.css_variables(),
        }

    def __str__(self) -> str:
        return self._mode

    def __repr__(self) -> str:
        return f"ThemeManager(mode={self._mode!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ThemeManager):
            return self._mode == other._mode
        return self._mode == other

    def __hash__(self) -> int:
        return hash(self._mode)


def _optional_name(value: Any, argument: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{argument} must be a non-empty string or None")
    return value.strip()


__all__ = ["ThemeManager"]
