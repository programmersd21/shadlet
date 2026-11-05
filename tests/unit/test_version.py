from __future__ import annotations

import json
import tomllib
from pathlib import Path

import shadlet as ui

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_is_consistent():
    with (ROOT / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)
    package = json.loads((ROOT / "packages/renderer/package.json").read_text())
    lock = json.loads((ROOT / "packages/renderer/package-lock.json").read_text())
    fixtures = json.loads(
        (ROOT / "packages/renderer/src/protocol/fixtures.json").read_text()
    )

    version = ui.__version__
    assert project["project"]["version"] == version
    assert package["version"] == version
    assert lock["version"] == version
    assert lock["packages"][""]["version"] == version
    init = next(item for item in fixtures["server"] if item["name"] == "init")
    assert init["value"]["app"]["version"] == version
