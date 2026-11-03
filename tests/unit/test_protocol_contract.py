import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from shadlet.protocol.models import (
    HelloMessage,
    Patch,
    ServerMessage,
    StatePatch,
    UpdateMessage,
)
from shadlet.protocol.validation import (
    parse_client_message,
    parse_server_message,
)

FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "renderer"
    / "src"
    / "protocol"
    / "fixtures.json"
)


def _fixtures() -> dict[str, list[dict[str, Any]]]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def test_server_fixtures_validate() -> None:
    for case in _fixtures()["server"]:
        message = parse_server_message(case["value"])
        assert message.model_dump(mode="json")["type"] == case["value"]["type"]


def test_client_fixtures_validate() -> None:
    for case in _fixtures()["client"]:
        message = parse_client_message(case["value"])
        assert message.model_dump(mode="json")["type"] == case["value"]["type"]


def test_unknown_message_type_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_client_message({"type": "desktop_result", "id": "x", "ok": True})


def test_unknown_properties_rejected_at_each_message_level() -> None:
    init = next(case for case in _fixtures()["server"] if case["name"] == "init")
    with pytest.raises(ValidationError):
        parse_server_message({**init["value"], "unexpected": True})
    with pytest.raises(ValidationError):
        parse_server_message(
            {
                **init["value"],
                "tree": {**init["value"]["tree"], "unexpected": True},
            }
        )
    with pytest.raises(ValidationError):
        parse_client_message({"type": "ping", "seq": 1, "unexpected": True})


def test_hello_rejects_inverted_protocol_range() -> None:
    with pytest.raises(ValidationError):
        HelloMessage(protocol_min=3, protocol_max=2)


def test_hello_rejects_relative_path() -> None:
    with pytest.raises(ValidationError):
        HelloMessage(protocol_min=2, protocol_max=2, path="relative")


def test_update_requires_known_ops() -> None:
    with pytest.raises(ValidationError):
        Patch.model_validate({"op": "explode", "path": ""})
    with pytest.raises(ValidationError):
        UpdateMessage(seq=1, patches=[Patch(op="remove", path="", index=-1)])
    assert StatePatch(op="delete", key="k").model_dump()["value"] is None


def test_server_message_alias_accepts_init() -> None:
    init = next(case for case in _fixtures()["server"] if case["name"] == "init")
    message: ServerMessage = parse_server_message(init["value"])
    assert message.type == "init"
