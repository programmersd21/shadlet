"""Session registry with token-based restoration and expiry."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shadlet.runtime.session import SendJson, Session

if TYPE_CHECKING:
    from shadlet.app.app import App
    from shadlet.web.config import WebConfig

logger = logging.getLogger("shadlet.sessions")


class SessionLimitError(RuntimeError):
    """Raised when the configured maximum number of sessions is reached."""


class SessionManager:
    """In-memory session registry.

    Sessions are keyed by an unguessable token. A reconnect that presents a
    valid, unexpired token restores the same session state. Sessions do not
    survive a server restart.
    """

    __slots__ = ("_app", "_config", "_sessions")

    def __init__(self, app: App, config: WebConfig) -> None:
        self._app = app
        self._config = config
        self._sessions: dict[str, Session] = {}

    def __len__(self) -> int:
        return len(self._sessions)

    def all(self) -> tuple[Session, ...]:
        return tuple(self._sessions.values())

    async def _purge_expired(self) -> None:
        for token, session in list(self._sessions.items()):
            if session.expired and not session.connected:
                self._sessions.pop(token, None)
                await session.close(reason="session expired")

    async def acquire(
        self,
        *,
        token: str | None,
        send_json: SendJson,
        platform: str = "web",
    ) -> Session:
        """Restore an existing session or create a new one and attach the transport."""
        await self._purge_expired()
        if token:
            existing = self._sessions.get(token)
            if existing is not None:
                if existing.closed:
                    self._sessions.pop(token, None)
                elif existing.connected or not existing.expired:
                    existing.attach(send_json, platform=platform)
                    logger.debug("restored session %s", existing.id)
                    return existing
        if len(self._sessions) >= self._config.max_sessions:
            raise SessionLimitError("maximum number of sessions reached")
        session = Session(
            self._app,
            send_json=send_json,
            platform=platform,
            ttl=self._config.session_ttl,
            max_events_per_second=self._config.max_events_per_second,
        )
        session.attach(send_json, platform=platform)
        self._sessions[session.token] = session
        logger.debug("created session %s", session.id)
        return session

    def release(self, session: Session) -> None:
        """Detach a transport while keeping the session available for reconnect."""
        session.detach()

    async def discard(self, session: Session, *, reason: str = "disconnected") -> None:
        self._sessions.pop(session.token, None)
        await session.close(reason=reason)

    async def sweep(self) -> None:
        """Close and remove sessions that have expired or closed."""
        for token, session in list(self._sessions.items()):
            if session.closed or (session.expired and not session.connected):
                self._sessions.pop(token, None)
                await session.close(reason="session expired")
                logger.debug("expired session %s", session.id)

    async def close_all(self) -> None:
        sessions = list(self._sessions.values())
        self._sessions.clear()
        for session in sessions:
            await session.close(reason="server shutting down")


__all__ = ["SessionLimitError", "SessionManager"]
