"""Small, explicit storage abstraction for uploaded application files.

The built-in adapter is process-local filesystem storage. It is intentionally
not distributed: applications running multiple workers must use a shared
adapter (for example an S3-compatible implementation) if uploads need to be
visible across processes.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable

_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class StorageError(ValueError):
    """Raised for invalid keys, unsafe paths, or storage limit violations."""


def sanitise_filename(filename: str, *, fallback: str = "upload") -> str:
    """Return a single safe filename component without touching the filesystem."""

    if not isinstance(filename, str):
        raise TypeError("filename must be a string")
    candidate = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    candidate = _UNSAFE_FILENAME.sub("-", candidate).strip(" .")
    if not candidate or candidate in {".", ".."}:
        candidate = fallback
    stem = candidate.split(".", 1)[0].lower()
    if stem in _RESERVED_NAMES:
        candidate = f"_{candidate}"
    return candidate[:255] or fallback


@dataclass(frozen=True, slots=True)
class StoredFile:
    key: str
    size: int
    path: Path


@runtime_checkable
class Storage(Protocol):
    """Minimal asynchronous-friendly storage contract."""

    def write(self, key: str, data: bytes, *, overwrite: bool = False) -> StoredFile:
        """Store bytes under ``key`` and return metadata."""
        ...

    def write_stream(
        self,
        key: str,
        stream: BinaryIO,
        *,
        overwrite: bool = False,
        chunk_size: int = 64 * 1024,
    ) -> StoredFile:
        """Store a readable binary stream without buffering it in memory."""
        ...

    def read(self, key: str) -> bytes:
        """Read a stored object."""
        ...

    def delete(self, key: str) -> None:
        """Delete a stored object if it exists."""
        ...

    def exists(self, key: str) -> bool:
        """Return whether ``key`` exists."""
        ...


class LocalStorage:
    """Filesystem storage rooted at one directory.

    Keys are relative POSIX-style paths. Absolute paths, ``..`` segments,
    backslashes and control characters are rejected. Writes are atomic within
    the destination filesystem.
    """

    __slots__ = ("_max_bytes", "_root")

    def __init__(self, root: str | os.PathLike[str], *, max_bytes: int = 10_000_000):
        if (
            isinstance(max_bytes, bool)
            or not isinstance(max_bytes, int)
            or max_bytes <= 0
        ):
            raise ValueError("max_bytes must be a positive integer")
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._max_bytes = max_bytes

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, key: str) -> Path:
        if not isinstance(key, str) or not key:
            raise StorageError("storage key must be a non-empty string")
        if "\\" in key or key.startswith("/") or ":" in key:
            raise StorageError("storage key must be a relative POSIX path")
        if any(ord(character) < 32 or ord(character) == 127 for character in key):
            raise StorageError("storage key cannot contain control characters")
        parts = key.split("/")
        if any(part in {"", ".", ".."} or part.endswith((" ", ".")) for part in parts):
            raise StorageError("storage key cannot contain empty or dot segments")
        candidate = self._root.joinpath(*parts)
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(self._root):
            raise StorageError("storage key resolves outside the storage root")
        return resolved

    def _write_file(
        self,
        key: str,
        *,
        source: bytes | BinaryIO | None = None,
        overwrite: bool,
        chunk_size: int = 64 * 1024,
    ) -> StoredFile:
        if (
            isinstance(chunk_size, bool)
            or not isinstance(chunk_size, int)
            or chunk_size < 1
        ):
            raise ValueError("chunk_size must be a positive integer")
        target = self._path(key)
        if target.exists() and not overwrite:
            raise FileExistsError(key)
        target.parent.mkdir(parents=True, exist_ok=True)

        temporary_path: Path | None = None
        size = 0
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                if isinstance(source, bytes):
                    size = len(source)
                    if size > self._max_bytes:
                        raise StorageError("uploaded file exceeds the storage limit")
                    temporary.write(source)
                elif source is not None:
                    while True:
                        chunk = source.read(chunk_size)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > self._max_bytes:
                            raise StorageError(
                                "uploaded file exceeds the storage limit"
                            )
                        temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, target)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        return StoredFile(key=key, size=size, path=target)

    def write(self, key: str, data: bytes, *, overwrite: bool = False) -> StoredFile:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data must be bytes")
        return self._write_file(key, source=bytes(data), overwrite=overwrite)

    def write_stream(
        self,
        key: str,
        stream: BinaryIO,
        *,
        overwrite: bool = False,
        chunk_size: int = 64 * 1024,
    ) -> StoredFile:
        if not hasattr(stream, "read"):
            raise TypeError("stream must be a binary readable object")
        return self._write_file(
            key,
            source=stream,
            overwrite=overwrite,
            chunk_size=chunk_size,
        )

    def read(self, key: str) -> bytes:
        path = self._path(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()


__all__ = [
    "LocalStorage",
    "Storage",
    "StorageError",
    "StoredFile",
    "sanitise_filename",
]
