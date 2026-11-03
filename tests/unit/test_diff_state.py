from __future__ import annotations

from typing import Any

import pytest
from shadlet._json import NotSerializableError
from shadlet.protocol.models import Node
from shadlet.runtime.diff import diff_trees, patch_path
from shadlet.state.state import State
from shadlet.state.store import StateStore


def _node(node_id: str, node_type: str = "Text", **kwargs: Any) -> Node:
    return Node(id=node_id, type=node_type, **kwargs)


def test_patch_path_handles_root_children_and_slots() -> None:
    assert patch_path("r") == ""
    assert patch_path("r.0.1") == "0.1"
    assert patch_path("r@header.0") == "@header.0"


def test_diff_replaces_when_text_changes() -> None:
    patches = diff_trees(_node("r", "#text", text="a"), _node("r", "#text", text="b"))
    assert len(patches) == 1
    assert patches[0].op == "replace"


def test_diff_uses_set_props_for_prop_changes() -> None:
    patches = diff_trees(
        _node("r", "Text", props={"value": "a"}),
        _node("r", "Text", props={"value": "b"}),
    )
    assert [patch.op for patch in patches] == ["set_props"]


def test_diff_uses_set_children_when_child_count_changes() -> None:
    old = _node("r", "Column", children=[_node("r.0")])
    new = _node("r", "Column", children=[_node("r.0"), _node("r.1")])
    patches = diff_trees(old, new)
    assert len(patches) == 1
    assert patches[0].op == "set_children"
    assert len(patches[0].children or []) == 2


def test_diff_replaces_when_type_changes() -> None:
    patches = diff_trees(_node("r", "Text"), _node("r", "Heading"))
    assert patches[0].op == "replace"
    assert patches[0].node is not None


def test_state_assignment_notifies_once() -> None:
    changes: list[str] = []
    state: State[int] = State(0, key="count", on_change=changes.append)
    state.value = 1
    state.value = 1
    state.update(lambda value: value + 1)
    assert state.value == 2
    assert changes == ["count", "count"]


def test_state_rejects_unserializable_values() -> None:
    state: State[object] = State(0, key="count", on_change=lambda _: None)
    with pytest.raises(NotSerializableError):
        state.value = object()


def test_in_place_mutation_does_not_notify() -> None:
    changes: list[str] = []
    state: State[list[int]] = State([1], key="items", on_change=changes.append)
    state.value.append(2)
    assert changes == []
    assert state.value == [1, 2]


def test_state_store_diff_detects_sets_and_deletes() -> None:
    store = StateStore()
    count = store.get("count", 0, lambda _: None)
    store.snapshot()
    count.value = 1
    store.sync("count")
    patches = store.diff({"count": 0, "stale": True})
    ops = {(patch.op, patch.key) for patch in patches}
    assert ops == {("set", "count"), ("delete", "stale")}
