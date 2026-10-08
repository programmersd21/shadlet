"""Runtime exceptions surfaced through the protocol."""

from __future__ import annotations


class ShadletError(Exception):
    """Base class for shadlet runtime errors."""


class RenderError(ShadletError):
    """The application returned an invalid or unserialisable component tree."""


class SessionError(ShadletError):
    """A session could not be created or resumed."""


__all__ = [
    "RenderError",
    "SessionError",
    "ShadletError",
]
