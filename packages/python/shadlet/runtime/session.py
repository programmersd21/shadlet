"""Session lifecycle, event ordering and incremental updates."""

from __future__ import annotations

import asyncio
import inspect
import secrets
import time
import traceback
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from shadlet.app.context import Context, RouteMatch
from shadlet.events.registry import EventRegistry
from shadlet.events.types import Event
from shadlet.protocol.models import (
    AppInfo,
    ErrorMessage,
    InitMessage,
    NavigationMessage,
    Node,
    StatePatch,
    ToastMessage,
    UpdateMessage,
)
from shadlet.runtime.diff import diff_trees
from shadlet.runtime.render import serialize_component
from shadlet.state.store import StateStore

if TYPE_CHECKING:
    from shadlet.app.app import App

SendJson = Callable[[dict[str, Any]], Awaitable[None]]


class Session:
    """One isolated user session."""

    __slots__ = (
        "_closed",
        "_connected",
        "_dirty",
        "_flush_task",
        "_last_client_seq",
        "_last_state",
        "_last_tree",
        "_lock",
        "_nav_task",
        "_pending_navigation",
        "_platform",
        "_send",
        "_send_lock",
        "_seq",
        "_toast_queue",
        "app",
        "created_at",
        "event_registry",
        "id",
        "last_seen",
        "route",
        "state_store",
        "token",
    )

    def __init__(
        self,
        app: App,
        *,
        send_json: SendJson,
        platform: str = "web",
        token: str | None = None,
    ) -> None:
        self.app = app
        self.id = secrets.token_urlsafe(12)
        self.token = token or secrets.token_urlsafe(32)
        self._send = send_json
        self._send_lock = asyncio.Lock()
        self._lock = asyncio.Lock()
        self._connected = True
        self._closed = False
        self._dirty = False
        self._flush_task: asyncio.Task[None] | None = None
        self._nav_task: asyncio.Task[None] | None = None
        self._pending_navigation: str | None = None
        self._platform = platform
        self._seq = 0
        self._last_client_seq = -1
        self._last_tree: Node | None = None
        self._last_state: dict[str, Any] = {}
        self._toast_queue: list[ToastMessage] = []
        self.state_store = StateStore()
        self.event_registry = EventRegistry()
        self.route: RouteMatch = app.match("/")
        self.created_at = time.monotonic()
        self.last_seen = self.created_at

    @property
    def connected(self) -> bool:
        return self._connected and not self._closed

    def attach(self, send_json: SendJson, *, platform: str) -> None:
        self._send = send_json
        self._connected = True
        self._closed = False
        self._platform = platform
        self.last_seen = time.monotonic()

    def detach(self) -> None:
        self._connected = False
        self.last_seen = time.monotonic()

    async def close(self, *, reason: str = "session closed") -> None:
        self._closed = True
        self._connected = False
        for task in (self._flush_task, self._nav_task):
            if task is not None:
                task.cancel()
        self._flush_task = None
        self._nav_task = None

    def send_toast(self, message: ToastMessage) -> None:
        if not self.connected:
            if len(self._toast_queue) >= 20:
                self._toast_queue.pop(0)
            self._toast_queue.append(message)
            return
        asyncio.create_task(self.send(message))

    async def send(self, message: BaseModel) -> None:
        if not self.connected:
            if isinstance(message, ToastMessage):
                if len(self._toast_queue) >= 20:
                    self._toast_queue.pop(0)
                self._toast_queue.append(message)
            return
        async with self._send_lock:
            try:
                await self._send(message.model_dump(mode="json"))
            except Exception:  # noqa: BLE001
                self._connected = False

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    async def _render(self) -> tuple[Node, dict[str, Any]]:
        self.event_registry.reset()
        context = Context(self, self.route)
        component = await self.app.render_page(self.route, context)
        tree = serialize_component(component, self)
        return tree, self.state_store.snapshot()

    async def send_init(self) -> None:
        if self._closed:
            return
        try:
            tree, state = await self._render()
        except Exception as error:  # noqa: BLE001
            await self._send_error(
                "render_error",
                str(error),
                details=traceback.format_exc() if self.app.debug else None,
                fatal=True,
            )
            return
        self._last_tree = tree
        self._last_state = state
        self._dirty = False
        message = InitMessage(
            app=AppInfo(
                title=self.app.title,
                version=self.app.version,
                theme=self.app.theme,  # type: ignore[arg-type]
                platform=self._platform,  # type: ignore[arg-type]
                icon=self.app.icon or "/logo.svg",
            ),
            route=self.route_info(),
            routes=self.app.routes(),
            tree=tree,
            state=state,
            features=[],
            session_token=self.token,
        )
        await self.send(message)
        for toast in self._toast_queue:
            await self.send(toast)
        self._toast_queue.clear()

    def route_info(self) -> Any:
        from shadlet.protocol.models import RouteInfo

        return RouteInfo(path=self.route.path, title=self.route.title)

    async def refresh(self) -> None:
        """Trigger an incremental update with the latest page render and diff patches."""
        if self._closed or not self._connected:
            return
        await self._send_update()

    async def _send_update(self, *, request_id: str | None = None) -> None:
        try:
            tree, state = await self._render()
        except Exception as error:  # noqa: BLE001
            await self._send_error(
                "render_error",
                str(error),
                request_id=request_id,
                details=traceback.format_exc() if self.app.debug else None,
            )
            return
        patches = diff_trees(self._last_tree, tree)
        state_patches: list[StatePatch] = self.state_store.diff(self._last_state)
        self._last_tree = tree
        self._last_state = state
        self._dirty = False
        if not patches and not state_patches:
            return
        await self.send(
            UpdateMessage(
                seq=self._next_seq(),
                request_id=request_id,
                patches=patches,
                state_patches=state_patches,
            )
        )

    async def flush(self) -> None:
        if not self.connected or self._closed:
            return
        if self._lock.locked():
            return
        async with self._lock:
            if not self._dirty:
                return
            await self._send_update()

    def _schedule_flush(self) -> None:
        if self._closed or not self.connected or self._lock.locked():
            return
        if self._flush_task is not None and not self._flush_task.done():
            return
        self._flush_task = asyncio.create_task(self.flush())

    def state_changed(self, key: str) -> None:
        self.state_store.sync(key)
        self._dirty = True
        self._schedule_flush()

    def request_navigation(self, path: str) -> None:
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("navigation path must start with '/'")
        self._pending_navigation = path
        if not self._lock.locked() and (
            self._nav_task is None or self._nav_task.done()
        ):
            self._nav_task = asyncio.create_task(self._flush_navigation())

    async def _flush_navigation(self) -> None:
        path = self._pending_navigation
        if path is None or self._closed:
            return
        async with self._lock:
            path = self._pending_navigation
            self._pending_navigation = None
            if path is not None:
                await self._navigate_locked(path)

    def _accept_seq(self, seq: int) -> bool:
        if seq <= self._last_client_seq:
            return False
        self._last_client_seq = seq
        return True

    async def handle_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        seq: int,
        request_id: str | None = None,
    ) -> None:
        if not self._accept_seq(seq):
            return
        async with self._lock:
            self.last_seen = time.monotonic()
            binding = self.event_registry.resolve(event_id)
            if binding is None:
                await self._send_error(
                    "unknown_event",
                    "the event is no longer valid; the component tree may have changed",
                    request_id=request_id,
                )
                return
            event = Event.from_payload(
                binding.event_name,
                binding.node_path,
                self.route.path,
                payload,
            )
            try:
                result = binding.handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as error:  # noqa: BLE001
                await self._send_error(
                    "handler_error",
                    str(error) or error.__class__.__name__,
                    request_id=request_id,
                    details=traceback.format_exc() if self.app.debug else None,
                )
            if self._pending_navigation is not None:
                path = self._pending_navigation
                self._pending_navigation = None
                await self._navigate_locked(path)
                return
            await self._send_update(request_id=request_id)

    async def handle_navigate(self, path: str, *, seq: int) -> None:
        if not self._accept_seq(seq):
            return
        async with self._lock:
            self.last_seen = time.monotonic()
            await self._navigate_locked(path)

    async def _navigate_locked(self, path: str) -> None:
        try:
            match = self.app.match(path)
        except Exception as error:  # noqa: BLE001
            await self._send_error("invalid_route", str(error))
            return
        self.route = match
        try:
            tree, state = await self._render()
        except Exception as error:  # noqa: BLE001
            await self._send_error(
                "render_error",
                str(error),
                details=traceback.format_exc() if self.app.debug else None,
            )
            return
        self._last_tree = tree
        self._last_state = state
        self._dirty = False
        await self.send(
            NavigationMessage(
                seq=self._next_seq(),
                route=self.route_info(),
                tree=tree,
                state=state,
            )
        )

    async def _send_error(
        self,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
        details: str | None = None,
        fatal: bool = False,
    ) -> None:
        await self.send(
            ErrorMessage(
                code=code,
                message=message,
                request_id=request_id,
                details=details,
                fatal=fatal,
            )
        )


__all__ = ["SendJson", "Session"]
