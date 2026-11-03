"""Metadata and asset access for separately packaged React extensions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path

_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
_VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True, slots=True)
class ExtensionManifest:
    """A React extension's packaged browser bundle and optional stylesheet.

    Register this object using the ``shadlet.extensions`` entry-point group.
    ``assets`` should be an ``importlib.resources.files(package) / "assets"``
    traversable so it works from an installed wheel.
    """

    name: str
    version: str
    assets: Traversable
    entrypoint: str = "index.js"
    stylesheet: str | None = None

    def __post_init__(self) -> None:
        if not _NAME.fullmatch(self.name):
            raise ValueError(f"invalid extension name: {self.name!r}")
        if not _VERSION.fullmatch(self.version):
            raise ValueError(f"invalid extension version: {self.version!r}")
        self._validate_asset_path(self.entrypoint)
        if self.stylesheet is not None:
            self._validate_asset_path(self.stylesheet)
        if not self.assets.is_dir():
            raise ValueError("extension assets must be a package resource directory")
        if not self.asset_exists(self.entrypoint):
            raise ValueError(f"extension entrypoint not found: {self.entrypoint!r}")
        if self.stylesheet is not None and not self.asset_exists(self.stylesheet):
            raise ValueError(f"extension stylesheet not found: {self.stylesheet!r}")

    @staticmethod
    def _validate_asset_path(path: str) -> None:
        parts = path.split("/")
        if not path or any(
            not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9._-]*", part)
            or part in {".", ".."}
            for part in parts
        ):
            raise ValueError(f"invalid extension asset path: {path!r}")

    def _asset(self, path: str) -> Traversable:
        self._validate_asset_path(path)
        if isinstance(self.assets, Path):
            root = self.assets.resolve()
            resolved = self.assets.joinpath(*path.split("/")).resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError(
                    "extension asset resolves outside its package directory"
                )
            return resolved
        return self.assets.joinpath(*path.split("/"))

    def asset_exists(self, path: str) -> bool:
        try:
            return self._asset(path).is_file()
        except FileNotFoundError:
            return False

    def read_asset(self, path: str) -> bytes:
        asset = self._asset(path)
        if not asset.is_file():
            raise FileNotFoundError(path)
        return asset.read_bytes()

    @property
    def entry_url(self) -> str:
        return f"/_shadlet_extensions/{self.name}/{self.entrypoint}"

    @property
    def stylesheet_url(self) -> str | None:
        if self.stylesheet is None:
            return None
        return f"/_shadlet_extensions/{self.name}/{self.stylesheet}"


__all__ = ["ExtensionManifest"]
