"""Application lifecycle, routing and page registration."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlsplit

from shadlet.app.context import Context, RouteMatch
from shadlet.app.uploads import UploadRequest
from shadlet.components.base import Component
from shadlet.components.enums import Theme
from shadlet.extensions import ExtensionManifest
from shadlet.fonts import FontManager
from shadlet.protocol.models import RouteInfo
from shadlet.theme import ThemeManager
from shadlet.version import __version__
from shadlet.web.config import Authenticator, WebConfig

PageFunction = Callable[[Context], Component | Awaitable[Component]]
UploadFunction = Callable[[UploadRequest], object | Awaitable[object]]


class RoutingError(ValueError):
    """Invalid route declaration or navigation."""


@dataclass(frozen=True, slots=True)
class Route:
    pattern: str
    title: str
    function: PageFunction
    regex: re.Pattern[str]
    static_segments: int
    param_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UploadRoute:
    path: str
    handler: UploadFunction
    max_bytes: int | None


def _normalise_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise RoutingError("route path must be a non-empty string")
    if not path.startswith("/"):
        raise RoutingError(f"route path must start with '/': {path!r}")
    if "?" in path or "#" in path or " " in path:
        raise RoutingError(
            f"route path cannot contain queries, fragments or spaces: {path!r}"
        )
    if "\\" in path:
        raise RoutingError(f"route path cannot contain backslashes: {path!r}")
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise RoutingError("route path cannot contain control characters")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"
    if "//" in path:
        raise RoutingError(f"route path cannot contain empty segments: {path!r}")
    segments = path.strip("/").split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise RoutingError(f"route path cannot contain dot segments: {path!r}")
    return path


def _decode_request_path(path: str) -> str:
    """Decode a browser path while rejecting ambiguous or unsafe escapes."""

    if "\\" in path:
        raise RoutingError("request path cannot contain backslashes")
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise RoutingError("request path cannot contain control characters")
    if re.search(r"%(?![0-9A-Fa-f]{2})", path):
        raise RoutingError("request path contains an invalid percent escape")
    lowered = path.lower()
    if any(token in lowered for token in ("%2f", "%5c", "%00")):
        raise RoutingError("request path contains an unsafe encoded character")
    try:
        decoded = unquote(path, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RoutingError("request path is not valid UTF-8") from error
    return decoded


def _compile_route(path: str) -> tuple[re.Pattern[str], int, tuple[str, ...]]:
    path = _normalise_path(path)
    if path == "/":
        return re.compile(r"^/$"), 0, ()
    segments = path.strip("/").split("/")
    pattern_parts: list[str] = []
    names: list[str] = []
    static = 0
    for segment in segments:
        match = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", segment)
        if match:
            name = match.group(1)
            if name in names:
                raise RoutingError(f"duplicate route parameter {name!r} in {path!r}")
            names.append(name)
            pattern_parts.append(f"(?P<{name}>[^/]+)")
        else:
            if "{" in segment or "}" in segment:
                raise RoutingError(f"invalid route segment {segment!r} in {path!r}")
            static += 1
            pattern_parts.append(re.escape(segment))
    return re.compile("^/" + "/".join(pattern_parts) + "$"), static, tuple(names)


class App:
    """A shadlet application.

    Pages are registered with :meth:`page`. An application instance is served
    by the web runtime.
    """

    def __init__(
        self,
        title: str = "shadlet app",
        *,
        icon: str | None = None,
        theme: Theme | str = Theme.LIGHT,
        debug: bool = False,
        version: str = __version__,
        toaster: bool = True,
        web: WebConfig | None = None,
        authenticate: Authenticator | None = None,
    ) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("app title must be a non-empty string")
        if theme not in tuple(Theme) and theme not in {"light", "dark", "system"}:
            raise ValueError("theme must be 'light', 'dark' or 'system'")
        if not isinstance(version, str) or not version:
            raise TypeError("app version must be a non-empty string")
        if not isinstance(toaster, bool):
            raise TypeError("toaster must be a boolean")
        if authenticate is not None and not callable(authenticate):
            raise TypeError("authenticate must be callable")
        self.title = title
        self.icon = icon
        self.fonts = FontManager()
        self.theme = ThemeManager(str(theme), fonts=self.fonts)
        self.debug = bool(debug)
        self.version = version
        self.toaster = toaster
        self.web = web if web is not None else WebConfig()
        self.authenticate = authenticate
        self._routes: list[Route] = []
        self._upload_routes: list[UploadRoute] = []
        self._extensions: dict[str, ExtensionManifest] = {}
        self._extensions_discovered = False
        self._not_found: PageFunction | None = None

    def page(
        self,
        path: str,
        *,
        title: str | None = None,
    ) -> Callable[[PageFunction], PageFunction]:
        normalised = _normalise_path(path)
        regex, static_segments, names = _compile_route(normalised)

        def decorator(function: PageFunction) -> PageFunction:
            if not callable(function):
                raise RoutingError("page must be a callable")
            for route in self._routes:
                if route.pattern == normalised:
                    raise RoutingError(f"duplicate route {normalised!r}")
                if route.regex.pattern == regex.pattern:
                    raise RoutingError(
                        f"route {normalised!r} conflicts with {route.pattern!r}"
                    )
            page_title = title or function.__name__.replace("_", " ").title()
            self._routes.append(
                Route(
                    pattern=normalised,
                    title=page_title,
                    function=function,
                    regex=regex,
                    static_segments=static_segments,
                    param_names=names,
                )
            )
            return function

        return decorator

    def not_found(self, function: PageFunction) -> PageFunction:
        if self._not_found is not None:
            raise RoutingError("a not-found page is already registered")
        if not callable(function):
            raise RoutingError("not-found page must be a callable")
        self._not_found = function
        return function

    def upload(
        self,
        path: str,
        *,
        max_bytes: int | None = None,
    ) -> Callable[[UploadFunction], UploadFunction]:
        """Register a multipart ``POST`` endpoint for bounded file uploads."""
        normalised = _normalise_path(path)
        if max_bytes is not None and (
            isinstance(max_bytes, bool)
            or not isinstance(max_bytes, int)
            or max_bytes <= 0
        ):
            raise ValueError("max_bytes must be a positive integer")
        if any(route.path == normalised for route in self._upload_routes):
            raise RoutingError(f"duplicate upload endpoint {normalised!r}")

        def decorator(function: UploadFunction) -> UploadFunction:
            if not callable(function):
                raise RoutingError("upload handler must be callable")
            self._upload_routes.append(UploadRoute(normalised, function, max_bytes))
            return function

        return decorator

    def add_extension(self, extension: ExtensionManifest) -> None:
        """Register a separately packaged React extension."""
        if not isinstance(extension, ExtensionManifest):
            raise TypeError("extension must be an ExtensionManifest")
        if extension.name in self._extensions:
            raise ValueError(f"extension is already registered: {extension.name}")
        self._extensions[extension.name] = extension

    def discover_extensions(self) -> None:
        """Load installed extensions declared through Python entry points."""
        if self._extensions_discovered:
            return
        from importlib.metadata import entry_points

        discovered: dict[str, ExtensionManifest] = {}
        for entry_point in entry_points(group="shadlet.extensions"):
            loaded = entry_point.load()
            if isinstance(loaded, ExtensionManifest):
                extension = loaded
            elif callable(loaded):
                extension = loaded()
            else:
                raise TypeError(
                    f"entry point {entry_point.name!r} did not return an ExtensionManifest"
                )
            if not isinstance(extension, ExtensionManifest):
                raise TypeError(
                    f"entry point {entry_point.name!r} did not return an ExtensionManifest"
                )
            if extension.name in self._extensions or extension.name in discovered:
                raise ValueError(f"extension is already registered: {extension.name}")
            discovered[extension.name] = extension
        self._extensions.update(discovered)
        self._extensions_discovered = True

    def routes(self) -> list[RouteInfo]:
        return [
            RouteInfo(path=route.pattern, title=route.title) for route in self._routes
        ]

    def match(self, path: str) -> RouteMatch:
        parsed = urlsplit(path)
        requested = _normalise_path(_decode_request_path(parsed.path))
        query_params = {
            key: values[-1]
            for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
        }
        for route in sorted(
            self._routes, key=lambda item: item.static_segments, reverse=True
        ):
            match = route.regex.fullmatch(requested)
            if match:
                params = dict(match.groupdict())
                return RouteMatch(
                    path=requested,
                    pattern=route.pattern,
                    title=route.title,
                    params=params,
                    query_params=query_params,
                )
        return RouteMatch(
            path=requested,
            pattern=requested,
            title="not found",
            not_found=True,
            query_params=query_params,
        )

    def _function_for(self, match: RouteMatch) -> PageFunction:
        if match.not_found:
            if self._not_found is not None:
                return self._not_found
            return _default_not_found
        for route in self._routes:
            if route.pattern == match.pattern:
                return route.function
        raise RoutingError(f"no page registered for {match.pattern!r}")

    async def render_page(self, match: RouteMatch, context: Context) -> Component:
        function = self._function_for(match)
        result = function(context)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, Component):
            raise TypeError(
                f"page {function.__name__!r} returned {type(result).__name__}; "
                "expected a shadlet Component"
            )
        return result

    def run(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8000,
        reload: bool = False,
    ) -> None:
        import os

        from shadlet.web.server import run_app

        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 0 <= port <= 65535
        ):
            raise ValueError("port must be an integer between 0 and 65535")
        port_name = next(
            (name for name in ("SHADLET_PORT", "PORT") if name in os.environ),
            None,
        )
        if port_name is None:
            target_port = port
        else:
            try:
                target_port = int(os.environ[port_name])
            except ValueError as error:
                raise ValueError(f"{port_name} must be an integer port") from error
            if not 0 <= target_port <= 65535:
                raise ValueError(f"{port_name} must be between 0 and 65535")
        run_app(self, host=host, port=target_port, reload=reload)


def _default_not_found(context: Context) -> Component:
    from shadlet.components.display import Card
    from shadlet.components.typography import Heading, Text
    from shadlet.layout.layout import Center

    return Center(
        Card(
            Heading("page not found", level=1),
            Text(f"no route matches {context.path}", variant="muted"),
        ),
        min_height="60vh",
        padding=24,
    )


__all__ = ["App", "PageFunction", "Route", "RoutingError", "UploadRoute"]
