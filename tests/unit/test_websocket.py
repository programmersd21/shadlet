import shadlet as ui
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient


def test_websocket_init_and_event():
    app = ui.App("ws test")

    @app.page("/")
    def home(ctx: ui.Context):
        count = ctx.state(0, key="count")

        def increment(event):
            count.value += 1

        return ui.Column(ui.Text(count), ui.Button("inc", on_click=increment))

    web_app = create_web_app(app)
    client = TestClient(web_app)
    with client.websocket_connect("/ws") as websocket:
        hello = {
            "type": "hello",
            "protocol_min": 1,
            "protocol_max": 1,
            "path": "/",
            "platform": "web",
        }
        websocket.send_json(hello)
        init = websocket.receive_json()
        assert init["type"] == "init"
        assert init["tree"]["type"] == "Column"
        event_id = init["tree"]["children"][1]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 2, "event_id": event_id, "payload": {}}
        )
        update = websocket.receive_json()
        assert update["type"] == "update"
        assert update["state_patches"][0]["value"] == 1
