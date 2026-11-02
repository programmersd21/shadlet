"""Application lifecycle, routing and page registration."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import unquote

from shadlet.app.context import Context, RouteMatch
from shadlet.components.base import Component
from shadlet.components.enums import Theme
from shadlet.protocol.models import RouteInfo

PageFunction = Callable[[Context], Component | Awaitable[Component]]


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


def _normalise_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise RoutingError("route path must be a non-empty string")
    if not path.startswith("/"):
        raise RoutingError(f"route path must start with '/': {path!r}")
    if "?" in path or "#" in path or " " in path:
        raise RoutingError(
            f"route path cannot contain queries, fragments or spaces: {path!r}"
        )
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"
    if "//" in path:
        raise RoutingError(f"route path cannot contain empty segments: {path!r}")
    return path


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
        version: str = "0.1.1",
        toaster: bool = True,
    ) -> None:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("app title must be a non-empty string")
        if theme not in tuple(Theme) and theme not in {"light", "dark", "system"}:
            raise ValueError("theme must be 'light', 'dark' or 'system'")
        self.title = title
        self.icon = icon
        self.theme = str(theme)
        self.debug = bool(debug)
        self.version = version
        self.toaster = bool(toaster)
        self._routes: list[Route] = []
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

    def routes(self) -> list[RouteInfo]:
        return [
            RouteInfo(path=route.pattern, title=route.title) for route in self._routes
        ]

    def match(self, path: str) -> RouteMatch:
        requested = _normalise_path(path)
        for route in sorted(
            self._routes, key=lambda item: item.static_segments, reverse=True
        ):
            match = route.regex.fullmatch(requested)
            if match:
                params = {
                    key: unquote(value) for key, value in match.groupdict().items()
                }
                return RouteMatch(
                    path=requested,
                    pattern=route.pattern,
                    title=route.title,
                    params=params,
                )
        return RouteMatch(
            path=requested,
            pattern=requested,
            title="not found",
            not_found=True,
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

        target_port = int(os.environ.get("SHADLET_PORT", str(port)))
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


__all__ = ["App", "PageFunction", "Route", "RoutingError"]
