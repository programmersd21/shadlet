from __future__ import annotations

import json
from pathlib import Path

import pytest
import shadlet as ui
from shadlet.components.icon_data import ICON_NAMES, LUCIDE_VERSION


def test_generated_icon_registry_is_complete_and_pinned():
    assert int(LUCIDE_VERSION.split(".", 1)[0]) >= 0
    assert len(ICON_NAMES) > 1_900
    assert len(set(ICON_NAMES)) == len(ICON_NAMES)
    assert "house" in ICON_NAMES
    assert "arrow-up-right" in ICON_NAMES
    assert "github" in ICON_NAMES


def test_icon_namespace_exposes_kebab_names_as_attributes():
    arrow = ui.icons.arrow_up_right(size=18, stroke_width=1.8)
    assert isinstance(arrow, ui.Icon)
    assert arrow.props["name"] == "arrow-up-right"
    assert arrow.props["size"] == 18
    assert arrow.props["strokeWidth"] == 1.8

    house = ui.icons.house(label="home")
    assert house.props["name"] == "house"
    assert house.props["label"] == "home"


def test_unknown_icon_names_fail_predictably():
    with pytest.raises(AttributeError, match="unknown icon"):
        _ = ui.icons.certainly_not_a_lucide_icon
    with pytest.raises(ui.ComponentError, match="unknown icon"):
        ui.Icon("certainly-not-a-lucide-icon")
    with pytest.raises(ui.ComponentError, match="unknown icon"):
        ui.Button("save", icon="certainly-not-a-lucide-icon")


def test_python_and_renderer_registries_come_from_the_same_source():
    data_path = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "renderer"
        / "src"
        / "shadlet"
        / "icon-data.generated.json"
    )
    if not data_path.exists():
        pytest.skip("renderer source tree is not present")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert data["lucideVersion"] == LUCIDE_VERSION
    assert tuple(data["names"]) == ICON_NAMES
    assert len(data["data"]) < len(data["names"])
    assert data["index"]["house"] == data["index"]["home"]


def test_structured_option_icons_are_validated():
    assert ui.MenuItem("home", "home", icon="house").icon == "house"
    assert ui.TabItem("home", "home", icon="house").icon == "house"
    assert ui.SidebarItem("home", icon="house").icon == "house"
    for factory in (
        lambda: ui.MenuItem("bad", "bad", icon="not-an-icon"),
        lambda: ui.TabItem("bad", "bad", icon="not-an-icon"),
        lambda: ui.SidebarItem("bad", icon="not-an-icon"),
    ):
        with pytest.raises(ui.ComponentError, match="unknown icon"):
            factory()
