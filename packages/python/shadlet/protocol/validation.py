"""Validated parsing helpers for wire messages."""

from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter, ValidationError

from shadlet.protocol.models import ClientMessage, ServerMessage

CLIENT_MESSAGE_ADAPTER: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)
SERVER_MESSAGE_ADAPTER: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)


def parse_client_message(value: Any) -> ClientMessage:
    """Validate an incoming browser message.

    Raises:
        ValidationError: if the message is not a valid client message.
    """

    return CLIENT_MESSAGE_ADAPTER.validate_python(value)


def parse_server_message(value: Any) -> ServerMessage:
    """Validate a server message. Useful for tests and tooling."""

    return SERVER_MESSAGE_ADAPTER.validate_python(value)


__all__ = [
    "CLIENT_MESSAGE_ADAPTER",
    "SERVER_MESSAGE_ADAPTER",
    "ValidationError",
    "parse_client_message",
    "parse_server_message",
]
