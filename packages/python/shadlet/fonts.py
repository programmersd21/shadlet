"""First-class custom font registration and CSS generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_FONT_FORMATS = {
    ".woff2": ("woff2", "font/woff2"),
    ".woff": ("woff", "font/woff"),
    ".ttf": ("truetype", "font/ttf"),
    ".otf": ("opentype", "font/otf"),
}

_WEIGHT_KEYWORDS = {"normal", "bold", "lighter", "bolder"}
_STYLE_VALUES = {"normal", "italic", "oblique"}
_DISPLAY_VALUES = {"auto", "block", "swap", "fallback", "optional"}
_DEFAULT_FONT_STACKS = {
    "Geist": (
        '"Geist Variable", "Geist", -apple-system, BlinkMacSystemFont, '
        '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    ),
    "Geist Mono": (
        '"Geist Mono Variable", "Geist Mono", ui-monospace, SFMono-Regular, '
        "Menlo, Monaco, Consolas, monospace"
    ),
}

_GENERIC_FALLBACKS = {
    "sans": "sans-serif",
    "serif": "serif",
    "mono": "monospace",
    "cursive": "cursive",
    "fantasy": "fantasy",
    "system": "system-ui",
}


def _validate_name(value: str, *, argument: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{argument} must be a non-empty string")
    return value.strip()


def _validate_source(source: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    source = source.strip()
    if any(ord(character) < 32 or ord(character) == 127 for character in source):
        raise ValueError("source cannot contain control characters")
    if "\\" in source and "://" not in source:
        # Native filesystem paths on Windows are normalised to slash form.
        source = source.replace("\\", "/")
    parsed = urlsplit(source)
    if "\\" in source:
        raise ValueError("source cannot contain backslashes")
    if (
        parsed.scheme
        and parsed.scheme not in {"http", "https"}
        and not re.fullmatch(r"[A-Za-z]", parsed.scheme)
    ):
        raise ValueError("source must use http, https or a relative path")
    if re.fullmatch(r"[A-Za-z]", parsed.scheme or ""):
        path = f"{parsed.scheme}:{parsed.path}"
    else:
        path = parsed.path or source
        if any(part in {".", ".."} for part in path.split("/") if part):
            raise ValueError("source cannot contain empty or dot path segments")
    if any(character in source for character in ('"', "'", ")", "<", ">")):
        raise ValueError("source contains characters that are not safe for CSS")
    suffix = Path(path).suffix.lower()
    if suffix not in _FONT_FORMATS:
        raise ValueError("source must use one of: " + ", ".join(sorted(_FONT_FORMATS)))
    # Local files are validated when they can be resolved. Remote and already
    # served URLs are intentionally not fetched by the framework.
    if (
        not parsed.scheme or re.fullmatch(r"[A-Za-z]", parsed.scheme or "")
    ) and not source.startswith("/"):
        candidates = _local_candidates(source)
        existing = [candidate for candidate in candidates if candidate.is_file()]
        if candidates and not existing:
            raise ValueError(f"font source does not exist: {source!r}")
        if existing:
            # Existing local files are accepted by absolute or project-relative
            # path. Traversal is already rejected above.
            pass
    return source


def _local_candidates(source: str) -> list[Path]:
    relative = source.lstrip("/")
    candidates = [Path(source), Path.cwd() / relative]
    if not source.startswith("/"):
        candidates.append(Path.cwd() / "assets" / relative)
    else:
        candidates.append(Path.cwd() / "assets" / relative)
    unique: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError):
            continue
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _allowed_root(path: Path) -> Path | None:
    roots = (Path.cwd().resolve(),)
    for root in roots:
        try:
            if path.is_relative_to(root):
                return root
        except ValueError:
            continue
    return None


def _validate_weight(weight: Any) -> str:
    if isinstance(weight, (bool, int)):
        value = str(weight)
    elif isinstance(weight, str):
        value = weight.strip()
    else:
        raise TypeError("weight must be a string or integer")
    if not value:
        raise ValueError("weight cannot be empty")
    if value in _WEIGHT_KEYWORDS:
        return value
    parts = value.split()
    if len(parts) == 1:
        if not parts[0].isdigit() or not 1 <= int(parts[0]) <= 1000:
            raise ValueError("weight must be between 1 and 1000")
        return parts[0]
    if len(parts) == 2:
        if not all(part.isdigit() for part in parts):
            raise ValueError("variable weight range must contain integers")
        first, second = (int(part) for part in parts)
        if not (1 <= first <= 1000 and 1 <= second <= 1000):
            raise ValueError("variable weight range must be between 1 and 1000")
        if first > second:
            raise ValueError("variable weight range must be ascending")
        return f"{first} {second}"
    raise ValueError("weight must be one value or an ascending range")


def _validate_style(style: Any) -> str:
    if not isinstance(style, str) or style not in _STYLE_VALUES:
        raise ValueError("style must be 'normal', 'italic' or 'oblique'")
    return style


def _validate_display(display: Any) -> str:
    if not isinstance(display, str) or display not in _DISPLAY_VALUES:
        raise ValueError("display must be a valid font-display value")
    return display


def _tuple_of_strings(value: Any, *, argument: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{argument} must be a string or sequence of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{argument} must contain non-empty strings")
        result.append(item.strip())
    return tuple(result)


def _css_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _mime_type(source: str) -> str:
    suffix = Path(urlsplit(source).path).suffix.lower()
    return _FONT_FORMATS.get(suffix, ("", "application/octet-stream"))[1]


@dataclass(frozen=True, slots=True)
class FontFace:
    """A validated descriptor for one ``@font-face`` rule."""

    family: str
    source: str
    weight: str = "400"
    style: str = "normal"
    display: str = "swap"
    fallback: tuple[str, ...] = ()
    subsets: tuple[str, ...] = ()
    unicode_range: str | None = None
    feature_settings: str | None = None
    variation_settings: str | None = None
    preload: bool = False
    alias: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "family", _validate_name(self.family, argument="family")
        )
        object.__setattr__(self, "source", _validate_source(self.source))
        object.__setattr__(self, "weight", _validate_weight(self.weight))
        object.__setattr__(self, "style", _validate_style(self.style))
        object.__setattr__(self, "display", _validate_display(self.display))
        object.__setattr__(
            self, "fallback", _tuple_of_strings(self.fallback, argument="fallback")
        )
        object.__setattr__(
            self, "subsets", _tuple_of_strings(self.subsets, argument="subsets")
        )
        if self.unicode_range is not None:
            if (
                not isinstance(self.unicode_range, str)
                or not self.unicode_range.strip()
            ):
                raise ValueError("unicode_range must be a non-empty string")
            object.__setattr__(self, "unicode_range", self.unicode_range.strip())
        for field_name in ("feature_settings", "variation_settings"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be a non-empty string")
            if isinstance(value, str):
                object.__setattr__(self, field_name, value.strip())
        if not isinstance(self.preload, bool):
            raise TypeError("preload must be a boolean")
        if self.alias is not None:
            object.__setattr__(
                self, "alias", _validate_name(self.alias, argument="alias")
            )

    @property
    def format_name(self) -> str:
        return _FONT_FORMATS[Path(urlsplit(self.source).path).suffix.lower()][0]

    @property
    def mime_type(self) -> str:
        return _mime_type(self.source)

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "source": self.source,
            "weight": self.weight,
            "style": self.style,
            "display": self.display,
            "fallback": list(self.fallback),
            "subsets": list(self.subsets),
            "unicodeRange": self.unicode_range,
            "featureSettings": self.feature_settings,
            "variationSettings": self.variation_settings,
            "preload": self.preload,
            "alias": self.alias,
            "format": self.format_name,
            "mimeType": self.mime_type,
        }

    def to_css(self) -> str:
        lines = [
            "@font-face {",
            f"  font-family: {_css_string(self.family)};",
            f"  src: url({_css_string(self.source)}) format({_css_string(self.format_name)});",
            f"  font-weight: {self.weight};",
            f"  font-style: {self.style};",
            f"  font-display: {self.display};",
        ]
        if self.unicode_range:
            lines.append(f"  unicode-range: {self.unicode_range};")
        if self.feature_settings:
            lines.append(f"  font-feature-settings: {self.feature_settings};")
        if self.variation_settings:
            lines.append(f"  font-variation-settings: {self.variation_settings};")
        lines.append("}")
        return "\n".join(lines)


class FontManager:
    """Session-independent registry of application fonts."""

    __slots__ = ("_faces",)

    def __init__(self) -> None:
        self._faces: dict[str, list[FontFace]] = {}

    def register(
        self,
        family: str,
        *,
        source: str,
        weight: Any = "400",
        style: str = "normal",
        display: str = "swap",
        fallback: Any = (),
        subsets: Any = (),
        unicode_range: str | None = None,
        feature_settings: str | None = None,
        variation_settings: str | None = None,
        preload: bool = False,
        alias: str | None = None,
        **extra: Any,
    ) -> FontFace:
        if extra:
            unknown = ", ".join(sorted(extra))
            raise ValueError(f"unknown font registration options: {unknown}")
        face = FontFace(
            family=family,
            source=source,
            weight=weight,
            style=style,
            display=display,
            fallback=fallback,
            subsets=subsets,
            unicode_range=unicode_range,
            feature_settings=feature_settings,
            variation_settings=variation_settings,
            preload=preload,
            alias=alias,
        )
        family_key = face.family
        for existing in self._faces.get(family_key, ()):
            if existing == face:
                raise ValueError(f"font is already registered: {family_key!r}")
        self._faces.setdefault(family_key, []).append(face)
        if face.alias:
            self._faces.setdefault(face.alias, []).append(face)
        return face

    def unregister(self, family: str) -> None:
        if family not in self._faces:
            raise ValueError(f"font is not registered: {family!r}")
        del self._faces[family]

    def families(self) -> list[str]:
        return sorted(self._faces)

    @property
    def registered(self) -> dict[str, list[FontFace]]:
        return {family: list(faces) for family, faces in self._faces.items()}

    @property
    def faces(self) -> list[FontFace]:
        result: list[FontFace] = []
        seen: set[int] = set()
        for faces in self._faces.values():
            for face in faces:
                identity = id(face)
                if identity not in seen:
                    seen.add(identity)
                    result.append(face)
        return result

    @property
    def preload_faces(self) -> list[FontFace]:
        return [face for face in self.faces if face.preload]

    @property
    def preload_urls(self) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        for face in self.preload_faces:
            if face.source not in seen:
                seen.add(face.source)
                urls.append(face.source)
        return urls

    def css(self) -> str:
        return "\n\n".join(face.to_css() for face in self.faces)

    def stylesheet(self) -> str:
        return self.css()

    def to_css(self) -> str:
        return self.css()

    def font_stack(
        self, family: str | None, *, generic: str = "sans-serif"
    ) -> str | None:
        if family is None:
            return None
        if family in _DEFAULT_FONT_STACKS:
            return _DEFAULT_FONT_STACKS[family]
        if family not in self._faces:
            # Allow built-in or externally available families to be named without
            # registration while still producing a valid CSS stack.
            return _css_string(family) + ", " + generic
        faces = self._faces[family]
        primary = faces[0].family
        fallbacks = list(faces[0].fallback) or [generic]
        parts = [
            _css_string(primary),
            *(
                _css_string(item)
                for item in fallbacks
                if item not in _GENERIC_FALLBACKS
            ),
        ]
        generic_values = [item for item in fallbacks if item in _GENERIC_FALLBACKS]
        if not generic_values:
            generic_values = [generic]
        parts.extend(_GENERIC_FALLBACKS.get(item, item) for item in generic_values)
        return ", ".join(parts)

    def to_init_payload(self) -> dict[str, Any]:
        return {
            "css": self.css(),
            "preloads": [
                {"href": face.source, "type": face.mime_type}
                for face in self.preload_faces
            ],
            "faces": [face.to_dict() for face in self.faces],
        }

    def __len__(self) -> int:
        return len(self.faces)


__all__ = ["FontFace", "FontManager"]
