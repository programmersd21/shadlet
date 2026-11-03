"""HTTP upload request types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UploadedFile:
    """A bounded file upload buffered for the duration of a handler call."""

    filename: str
    content_type: str | None
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)


@dataclass(frozen=True, slots=True)
class UploadRequest:
    """Parsed multipart form fields and files."""

    fields: Mapping[str, str]
    files: Mapping[str, tuple[UploadedFile, ...]]


__all__ = ["UploadRequest", "UploadedFile"]
