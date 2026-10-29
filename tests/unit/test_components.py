import pytest
import shadlet as ui
from shadlet.components.base import ComponentError
from shadlet.state.state import State


def test_button_variants():
    b = ui.Button("x", variant="outline", size="sm")
    assert b.props["variant"] == "outline"
    assert b.props["size"] == "sm"
    with pytest.raises(ComponentError):
        ui.Button("x", variant="nope")


def test_state_rejects_callback():
    with pytest.raises(Exception):  # noqa: B017
        State(lambda x: x, key="bad", on_change=lambda k: None)


def test_grid_responsive():
    g = ui.Grid(columns=ui.Responsive(base=1, sm=2, lg=3))
    assert g.props["columns"] == {"base": 1, "sm": 2, "lg": 3}


def test_invalid_child():
    with pytest.raises(ComponentError):
        ui.Column(True)


def test_option_normalization():
    s = ui.Select(["a", "b"], value="a")
    assert s.props["options"][0]["value"] == "a"
    with pytest.raises(ComponentError):
        ui.Select([{"value": "a"}])  # missing label
