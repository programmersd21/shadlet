"""Web runtime configuration and connection authentication types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ConnectionRequest:
    """Information available before a session is created.

    ``origin`` is the browser-supplied Origin header, which is advisory and is
    not an authentication mechanism. ``token`` is the session token presented in
    the handshake, if any.
    """

    origin: str | None
    host: str | None
    path: str
    token: str | None
    headers: Mapping[str, str] = field(default_factory=dict)
    query: Mapping[str, str] = field(default_factory=dict)


Authenticator = Callable[[ConnectionRequest], bool | Awaitable[bool]]
"""Return ``True`` to accept a connection, or ``False`` to reject it."""


@dataclass(frozen=True, slots=True)
class WebConfig:
    """Resource limits and origin policy for the web runtime.

    ``allowed_origins`` defaults to ``None``, which accepts same-origin browser
    connections and localhost origins, plus non-browser clients that omit the
    Origin header. Set it explicitly to a tuple of origins for production
    deployments behind a reverse proxy. The single value ``"*"`` disables origin
    validation and should only be used when another layer enforces it.
    """

    allowed_origins: tuple[str, ...] | None = None
    session_ttl: float = 3600.0
    max_sessions: int = 1000
    max_message_bytes: int = 1_000_000
    max_upload_bytes: int = 10_000_000
    max_events_per_second: int = 200
    handshake_timeout: float = 10.0
    sweep_interval: float = 30.0

    def __post_init__(self) -> None:
        if self.session_ttl <= 0:
            raise ValueError("session_ttl must be greater than zero")
        if self.max_sessions <= 0:
            raise ValueError("max_sessions must be greater than zero")
        if self.max_message_bytes <= 0:
            raise ValueError("max_message_bytes must be greater than zero")
        if self.max_upload_bytes <= 0:
            raise ValueError("max_upload_bytes must be greater than zero")
        if self.max_events_per_second <= 0:
            raise ValueError("max_events_per_second must be greater than zero")
        if self.handshake_timeout <= 0:
            raise ValueError("handshake_timeout must be greater than zero")
        if self.sweep_interval <= 0:
            raise ValueError("sweep_interval must be greater than zero")
        if self.allowed_origins is not None:
            origins = tuple(
                origin.strip() for origin in self.allowed_origins if origin.strip()
            )
            if "*" in origins and len(origins) != 1:
                raise ValueError(
                    "'*' must be the only allowed origin when origin validation is disabled"
                )
            object.__setattr__(
                self,
                "allowed_origins",
                origins,
            )


__all__ = ["Authenticator", "ConnectionRequest", "WebConfig"]
