import pytest
from pydantic import ValidationError
from shadlet.protocol.models import (
    Node,
    Patch,
    StatePatch,
    UpdateMessage,
)
from shadlet.protocol.version import ProtocolIncompatibleError, negotiate_protocol


def test_node_rejects_text_with_children():
    with pytest.raises(ValidationError):
        Node(id="r", type="#text", text="x", children=[Node(id="r.0", type="Text")])


def test_patch_requires_fields():
    with pytest.raises(ValidationError):
        Patch(op="replace", path="")
    patch = Patch(op="replace", path="", node=Node(id="r", type="Text"))
    assert patch.node is not None


def test_negotiate_protocol():
    assert negotiate_protocol(1, 2).version == 2
    with pytest.raises(ProtocolIncompatibleError):
        negotiate_protocol(1, 1)


def test_state_patch_serialization():
    patch = StatePatch(op="set", key="count", value=5)
    assert patch.model_dump()["value"] == 5
    assert StatePatch(op="delete", key="count").model_dump()["op"] == "delete"


def test_update_message_round_trip():
    message = UpdateMessage(
        seq=1,
        patches=[Patch(op="replace", path="", node=Node(id="r", type="Text"))],
        state_patches=[StatePatch(op="set", key="k", value="v")],
    )
    data = message.model_dump()
    assert data["type"] == "update"
    assert data["patches"][0]["op"] == "replace"
