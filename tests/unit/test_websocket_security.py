from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import shadlet as ui
from shadlet.web import server
from shadlet.web.config import ConnectionRequest, WebConfig
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

HELLO = {
    "type": "hello",
    "protocol_min": 2,
    "protocol_max": 2,
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


def test_origin_wildcard_must_be_standalone():
    with pytest.raises(ValueError, match="must be the only allowed origin"):
        WebConfig(allowed_origins=("*", "https://good.example"))


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


def test_malformed_messages_consume_rate_limit_capacity():
    client = TestClient(
        create_web_app(_counter_app(web=WebConfig(max_events_per_second=1)))
    )
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        assert websocket.receive_json()["type"] == "init"
        websocket.send_text("{not json")
        assert websocket.receive_json()["code"] == "invalid_message"
        websocket.send_text("{still not json")
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


def test_invalid_sequence_frames_consume_rate_limit_capacity():
    client = TestClient(
        create_web_app(_counter_app(web=WebConfig(max_events_per_second=1)))
    )
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        init = websocket.receive_json()
        event_id = init["tree"]["children"][1]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": -1, "event_id": event_id, "payload": {}}
        )
        websocket.send_text("{not json")
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


def test_oversized_message_closes_connection():
    app = _counter_app(web=WebConfig(max_message_bytes=64))
    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("x" * 200)
        assert websocket.receive_json()["code"] == "message_too_large"
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


def test_uvicorn_transport_frame_limit_uses_web_config(monkeypatch: pytest.MonkeyPatch):
    kwargs: dict[str, object] = {}
    monkeypatch.setattr(server, "find_available_port", lambda host, port: port)
    monkeypatch.setattr(
        server.uvicorn,
        "run",
        lambda *args, **options: kwargs.update(options),
    )
    server.run_app(_counter_app(web=WebConfig(max_message_bytes=1234)))
    assert kwargs["ws_max_size"] == 1234


def test_file_icon_is_served_only_from_public_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    assets = tmp_path / "assets"
    assets.mkdir()
    public_icon = assets / "icon.svg"
    public_icon.write_text("<svg>public</svg>", encoding="utf-8")
    secret_icon = tmp_path / "secret.svg"
    secret_icon.write_text("<svg>secret</svg>", encoding="utf-8")

    public_client = TestClient(create_web_app(_counter_app(icon="assets/icon.svg")))
    response = public_client.get("/_app_icon")
    assert response.status_code == 200
    assert "public" in response.text

    private_client = TestClient(create_web_app(_counter_app(icon="../secret.svg")))
    response = private_client.get("/_app_icon")
    assert response.status_code in {200, 404}
    assert "secret" not in response.text


def test_production_render_errors_hide_internal_details():
    app = ui.App("render failure")

    @app.page("/")
    def home(ctx: ui.Context):
        raise RuntimeError("database password")

    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        error = websocket.receive_json()
        assert error["code"] == "render_error"
        assert error["message"] == "page rendering failed"
        assert "database password" not in error["message"]
        assert error["details"] is None


@pytest.mark.parametrize(
    ("debug", "expected_message", "has_details"),
    [
        (False, "event handler failed", False),
        (True, "private event detail", True),
    ],
)
def test_event_errors_only_expose_details_in_debug_mode(
    debug: bool, expected_message: str, has_details: bool
):
    app = ui.App("event failure", debug=debug)

    @app.page("/")
    def home(ctx: ui.Context):
        def fail(event):
            raise RuntimeError("private event detail")

        return ui.Button("fail", on_click=fail)

    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(HELLO)
        init = websocket.receive_json()
        event_id = init["tree"]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 1, "event_id": event_id, "payload": {}}
        )
        error = websocket.receive_json()
        assert error["code"] == "handler_error"
        assert error["message"] == expected_message
        assert bool(error["details"]) is has_details


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
