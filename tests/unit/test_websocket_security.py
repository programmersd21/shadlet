from __future__ import annotations

import asyncio

import pytest
import shadlet as ui
from shadlet.web.config import ConnectionRequest, WebConfig
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

HELLO = {
    "type": "hello",
    "protocol_min": 1,
    "protocol_max": 1,
    "path": "/",
    "platform": "web",
}


def _counter_app(**kwargs: object) -> ui.App:
    app = ui.App("ws test", **kwargs)  # type: ignore[arg-type]

    @app.page("/")
    def home(ctx: ui.Context):
        count = ctx.state(0, key="count")

        def increment(event):
            count.value += 1

        return ui.Column(ui.Text(count), ui.Button("inc", on_click=increment))

    return app


def test_handshake_requires_hello_first():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "event", "seq": 1, "event_id": "x"})
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "invalid_handshake"
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()


def test_protocol_incompatible_is_rejected():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {"type": "hello", "protocol_min": 99, "protocol_max": 100, "path": "/"}
        )
        error = websocket.receive_json()
        assert error["code"] == "protocol_incompatible"
        assert error["fatal"] is True


def test_origin_validation_rejects_unknown_origin():
    app = _counter_app(web=WebConfig(allowed_origins=("https://good.example",)))
    client = TestClient(create_web_app(app))
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/ws", headers={"origin": "https://evil.example"}),
    ):
        pass


def test_origin_validation_accepts_configured_origin():
    app = _counter_app(web=WebConfig(allowed_origins=("https://good.example",)))
    client = TestClient(create_web_app(app))
    with client.websocket_connect(
        "/ws", headers={"origin": "https://good.example"}
    ) as websocket:
        websocket.send_json(HELLO)
        assert websocket.receive_json()["type"] == "init"


def test_authenticator_can_reject_connections():
    def authenticate(request: ConnectionRequest) -> bool:
        return request.query.get("key") == "secret"

    app = _counter_app(authenticate=authenticate)
    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        assert websocket.receive_json()["code"] == "unauthorized"
    with client.websocket_connect("/ws?key=secret") as websocket:
        websocket.send_json(HELLO)
        assert websocket.receive_json()["type"] == "init"


def test_authenticator_can_be_async():
    async def authenticate(request: ConnectionRequest) -> bool:
        await asyncio.sleep(0)
        return True

    client = TestClient(create_web_app(_counter_app(authenticate=authenticate)))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        assert websocket.receive_json()["type"] == "init"


def test_session_token_restores_state_after_reconnect():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        init = websocket.receive_json()
        token = init["session_token"]
        event_id = init["tree"]["children"][1]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 2, "event_id": event_id, "payload": {}}
        )
        update = websocket.receive_json()
        assert update["state_patches"][0]["value"] == 1

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({**HELLO, "token": token})
        reconnected = websocket.receive_json()
        assert reconnected["session_token"] == token
        assert reconnected["state"]["/:count"] == 1


def test_sessions_are_isolated():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as first:
        first.send_json(HELLO)
        init_a = first.receive_json()
        with client.websocket_connect("/ws") as second:
            second.send_json(HELLO)
            init_b = second.receive_json()
            assert init_a["session_token"] != init_b["session_token"]

            event_id = init_a["tree"]["children"][1]["events"]["click"]
            first.send_json(
                {"type": "event", "seq": 2, "event_id": event_id, "payload": {}}
            )
            assert first.receive_json()["state_patches"][0]["value"] == 1
            second.send_json({"type": "navigate", "seq": 2, "path": "/"})
            assert second.receive_json()["state"]["/:count"] == 0


def test_invalid_message_after_handshake_is_reported():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        websocket.receive_json()
        websocket.send_text("{not json")
        error = websocket.receive_json()
        assert error["code"] == "invalid_message"
        # The connection remains usable.
        websocket.send_json({"type": "ping", "seq": 5})
        assert websocket.receive_json() == {"type": "pong", "seq": 5}


def test_oversized_message_closes_connection():
    app = _counter_app(web=WebConfig(max_message_bytes=64))
    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("x" * 200)
        assert websocket.receive_json()["code"] == "message_too_large"
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


def test_navigation_uses_initial_message_for_non_root_path():
    app = ui.App("routes")

    @app.page("/about")
    def about(ctx: ui.Context):
        return ui.Text("about")

    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({**HELLO, "path": "/about"})
        message = websocket.receive_json()
        assert message["type"] == "init"
        assert message["route"]["path"] == "/about"


def test_reconnected_client_can_restart_event_sequence():
    client = TestClient(create_web_app(_counter_app()))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        init = websocket.receive_json()
        token = init["session_token"]
        event_id = init["tree"]["children"][1]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 2, "event_id": event_id, "payload": {}}
        )
        assert websocket.receive_json()["state_patches"][0]["value"] == 1

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({**HELLO, "token": token})
        reconnected = websocket.receive_json()
        event_id = reconnected["tree"]["children"][1]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 2, "event_id": event_id, "payload": {}}
        )
        update = websocket.receive_json()
        assert update["state_patches"][0]["value"] == 2
