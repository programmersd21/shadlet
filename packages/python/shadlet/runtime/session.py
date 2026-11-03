"""Session lifecycle, event ordering and incremental updates."""

from __future__ import annotations

import asyncio
import inspect
import logging
import secrets
import time
import traceback
from collections.abc import Awaitable, Callable, Coroutine
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
from shadlet.protocol.version import PROTOCOL_VERSION
from shadlet.runtime.diff import diff_trees
from shadlet.runtime.render import serialize_component
from shadlet.state.store import StateStore

if TYPE_CHECKING:
    from shadlet.app.app import App

logger = logging.getLogger("shadlet.session")

SendJson = Callable[[dict[str, Any]], Awaitable[None]]

_MAX_QUEUED_TOASTS = 20


class Session:
    """One isolated user session."""

    __slots__ = (
        "_closed",
        "_connected",
        "_dirty",
        "_event_tokens",
        "_event_tokens_at",
        "_flush_task",
        "_generation",
        "_last_client_seq",
        "_last_state",
        "_last_tree",
        "_lock",
        "_max_events_per_second",
        "_nav_task",
        "_pending_navigation",
        "_platform",
        "_send",
        "_send_lock",
        "_seq",
        "_tasks",
        "_toast_queue",
        "app",
        "created_at",
        "event_registry",
        "id",
        "last_seen",
        "route",
        "state_store",
        "token",
        "ttl",
    )

    def __init__(
        self,
        app: App,
        *,
        send_json: SendJson,
        platform: str = "web",
        token: str | None = None,
        ttl: float = 3600.0,
        max_events_per_second: int = 200,
    ) -> None:
        self.app = app
        self.id = secrets.token_urlsafe(12)
        self.token = token or secrets.token_urlsafe(32)
        self.ttl = ttl
        self._send = send_json
        self._send_lock = asyncio.Lock()
        self._lock = asyncio.Lock()
        self._connected = True
        self._closed = False
        self._dirty = False
        self._generation = 0
        self._flush_task: asyncio.Task[None] | None = None
        self._nav_task: asyncio.Task[None] | None = None
        self._pending_navigation: str | None = None
        self._platform = platform
        self._seq = 0
        self._last_client_seq = -1
        self._last_tree: Node | None = None
        self._last_state: dict[str, Any] = {}
        self._toast_queue: list[ToastMessage] = []
        self._tasks: set[asyncio.Task[Any]] = set()
        self._max_events_per_second = max_events_per_second
        self._event_tokens = float(max_events_per_second)
        self._event_tokens_at = time.monotonic()
        self.state_store = StateStore()
        self.event_registry = EventRegistry()
        self.route: RouteMatch = app.match("/")
        self.created_at = time.monotonic()
        self.last_seen = self.created_at

    @property
    def connected(self) -> bool:
        return self._connected and not self._closed

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def expired(self) -> bool:
        return time.monotonic() - self.last_seen > self.ttl

    @property
    def generation(self) -> int:
        return self._generation

    def touch(self) -> None:
        self.last_seen = time.monotonic()

    def attach(self, send_json: SendJson, *, platform: str) -> int:
        """Bind a new transport and return its connection generation."""
        for task in (self._flush_task, self._nav_task):
            if task is not None and not task.done():
                task.cancel()
        self._flush_task = None
        self._nav_task = None
        self._pending_navigation = None
        self._last_client_seq = -1
        self._generation += 1
        self._send = send_json
        self._connected = True
        self._closed = False
        self._platform = platform
        self.touch()
        return self._generation

    def is_current(self, generation: int) -> bool:
        return self._generation == generation and self.connected

    def detach(self, generation: int | None = None) -> None:
        if generation is not None and generation != self._generation:
            return
        self._connected = False
        self.touch()
        self._pending_navigation = None
        for task in (self._flush_task, self._nav_task):
            if task is not None:
                task.cancel()
        self._flush_task = None
        self._nav_task = None

    async def close(self, *, reason: str = "session closed") -> None:
        if self._closed:
            return
        self._closed = True
        self._connected = False
        tasks = [task for task in self._tasks if not task.done()]
        for task in (self._flush_task, self._nav_task):
            if task is not None and not task.done():
                tasks.append(task)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._flush_task = None
        self._nav_task = None
        logger.debug("session %s closed: %s", self.id, reason)

    def _task_done(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            logger.error(
                "unhandled session task error",
                exc_info=(type(error), error, error.__traceback__),
            )

    def _spawn(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._task_done)
        return task

    def send_toast(self, message: ToastMessage) -> None:
        if not self.connected:
            if len(self._toast_queue) >= _MAX_QUEUED_TOASTS:
                self._toast_queue.pop(0)
            self._toast_queue.append(message)
            return
        self._spawn(self.send(message))

    async def send(self, message: BaseModel) -> None:
        if not self.connected:
            if isinstance(message, ToastMessage):
                if len(self._toast_queue) >= _MAX_QUEUED_TOASTS:
                    self._toast_queue.pop(0)
                self._toast_queue.append(message)
            return
        send_json = self._send
        generation = self._generation
        async with self._send_lock:
            try:
                await send_json(message.model_dump(mode="json"))
            except Exception:  # noqa: BLE001
                logger.warning(
                    "failed to send %s message on session %s",
                    getattr(message, "type", type(message).__name__),
                    self.id,
                )
                self.detach(generation)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    async def _render(self) -> tuple[Node, dict[str, Any]]:
        self.event_registry.reset()
        context = Context(self, self.route)
        component = await self.app.render_page(self.route, context)
        tree = serialize_component(component, self)
        return tree, self.state_store.snapshot()

    async def send_init(self, *, protocol: int = PROTOCOL_VERSION) -> None:
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
            protocol=protocol,
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
        while self._toast_queue and self.connected:
            toast = self._toast_queue.pop(0)
            await self.send(toast)

    async def start(self, path: str = "/", *, protocol: int = PROTOCOL_VERSION) -> None:
        """Resolve ``path`` and send the initial render."""
        try:
            self.route = self.app.match(path)
        except Exception as error:  # noqa: BLE001
            await self._send_error("invalid_route", str(error), fatal=True)
            return
        await self.send_init(protocol=protocol)

    def route_info(self) -> Any:
        from shadlet.protocol.models import RouteInfo

        return RouteInfo(path=self.route.path, title=self.route.title)

    async def refresh(self) -> None:
        """Trigger an incremental update with the latest page render and diff patches."""
        if self._closed or not self._connected:
            return
        async with self._lock:
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
        async with self._lock:
            if not self._dirty:
                return
            await self._send_update()

    def _schedule_flush(self) -> None:
        if self._closed or not self.connected:
            return
        if self._flush_task is not None and not self._flush_task.done():
            return
        self._flush_task = self._spawn(self.flush())

    def state_changed(self, key: str) -> None:
        self.state_store.sync(key)
        self._dirty = True
        self._schedule_flush()

    def request_navigation(self, path: str) -> None:
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("navigation path must start with '/'")
        self._pending_navigation = path
        if self._nav_task is None or self._nav_task.done():
            self._nav_task = self._spawn(self._flush_navigation())

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
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            return False
        if seq <= self._last_client_seq:
            return False
        self._last_client_seq = seq
        return True

    def allow_message(self) -> bool:
        """Consume one token from the per-session message rate limiter."""
        now = time.monotonic()
        rate = float(self._max_events_per_second)
        elapsed = now - self._event_tokens_at
        if elapsed > 0:
            self._event_tokens = min(rate, self._event_tokens + elapsed * rate)
            self._event_tokens_at = now
        if self._event_tokens < 1:
            return False
        self._event_tokens -= 1
        return True

    async def handle_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        seq: int,
        request_id: str | None = None,
    ) -> None:
        if self._closed or not self.connected:
            return
        if not self._accept_seq(seq):
            return
        if not self.allow_message():
            await self._send_error(
                "rate_limited",
                "event rate limit exceeded; slow down or reconnect",
                request_id=request_id,
            )
            return
        if not isinstance(payload, dict):
            await self._send_error(
                "invalid_payload",
                "event payload must be a JSON object",
                request_id=request_id,
            )
            return
        async with self._lock:
            self.touch()
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
            except Exception as error:
                logger.exception("event handler failed for %s", binding.event_name)
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
        if self._closed or not self.connected:
            return
        if not self._accept_seq(seq):
            return
        async with self._lock:
            self.touch()
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
