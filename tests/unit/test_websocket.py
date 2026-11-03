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
            "protocol_min": 2,
            "protocol_max": 2,
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


def test_query_state_tracks_url_and_popstate_navigation():
    app = ui.App("query state")

    @app.page("/search")
    def search(ctx: ui.Context):
        page = ctx.query_state("page", 1, history="push")

        def next_page(event):
            page.value += 1

        return ui.Button(str(page.value), on_click=next_page)

    client = TestClient(create_web_app(app))
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {
                "type": "hello",
                "protocol_min": 2,
                "protocol_max": 2,
                "path": "/search?page=4",
                "platform": "web",
            }
        )
        init = websocket.receive_json()
        assert init["route"]["path"] == "/search?page=4"
        event_id = init["tree"]["events"]["click"]
        websocket.send_json(
            {"type": "event", "seq": 1, "event_id": event_id, "payload": {}}
        )
        update = websocket.receive_json()
        assert update["type"] == "update"
        assert update["url"] == "/search?page=5"
        assert update["url_mode"] == "push"
        assert update["state_patches"][0]["value"] == 5

        websocket.send_json(
            {
                "type": "navigate",
                "seq": 2,
                "path": "/search?page=8",
                "replace": True,
            }
        )
        navigation = websocket.receive_json()
        assert navigation["type"] == "navigation"
        assert navigation["route"]["path"] == "/search?page=8"
        assert navigation["state"]["/search:query:page"] == 8
        assert navigation["replace"] is True

        websocket.send_json(
            {"type": "navigate", "seq": 3, "path": "/search?page=invalid"}
        )
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "invalid_route"
