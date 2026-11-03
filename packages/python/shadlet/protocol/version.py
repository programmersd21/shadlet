"""Protocol versioning and negotiation."""

from __future__ import annotations

from dataclasses import dataclass

PROTOCOL_VERSION = 2
SUPPORTED_PROTOCOL_VERSIONS: tuple[int, ...] = (2,)


class ProtocolIncompatibleError(RuntimeError):
    """Raised when the client and server cannot agree on a protocol version."""

    def __init__(self, client_min: int, client_max: int) -> None:
        self.client_min = client_min
        self.client_max = client_max
        super().__init__(
            "protocol incompatible: client supports "
            f"{client_min}..{client_max}, server supports "
            f"{min(SUPPORTED_PROTOCOL_VERSIONS)}..{max(SUPPORTED_PROTOCOL_VERSIONS)}"
        )


@dataclass(frozen=True, slots=True)
class NegotiatedProtocol:
    version: int


def negotiate_protocol(client_min: int, client_max: int) -> NegotiatedProtocol:
    """Choose the highest protocol version supported by both peers.

    Raises:
        ProtocolIncompatibleError: if the ranges do not overlap.
    """

    if client_min > client_max:
        raise ProtocolIncompatibleError(client_min, client_max)
    common = [
        version
        for version in SUPPORTED_PROTOCOL_VERSIONS
        if client_min <= version <= client_max
    ]
    if not common:
        raise ProtocolIncompatibleError(client_min, client_max)
    return NegotiatedProtocol(version=max(common))
