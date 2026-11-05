"""HTTP upload request types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shadlet.storage import sanitise_filename

if TYPE_CHECKING:
    from shadlet.storage import Storage, StoredFile


@dataclass(frozen=True, slots=True)
class UploadedFile:
    """A bounded file upload buffered for the duration of a handler call."""

    filename: str
    content_type: str | None
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def safe_filename(self) -> str:
        """Return a filename safe to use as one storage key component."""

        return sanitise_filename(self.filename)

    def save_to(self, storage: Storage, *, key: str | None = None) -> StoredFile:
        """Store this upload using the application's storage adapter."""

        return storage.write(key or self.safe_filename, self.data)


@dataclass(frozen=True, slots=True)
class UploadRequest:
    """Parsed multipart form fields and files."""

    fields: Mapping[str, str]
    files: Mapping[str, tuple[UploadedFile, ...]]


__all__ = ["UploadRequest", "UploadedFile"]
