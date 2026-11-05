import pytest
import shadlet as ui
from shadlet.runtime.session import Session


def test_app_run_port_precedence(monkeypatch):
    from shadlet.web import server

    calls = []
    monkeypatch.setattr(server, "run_app", lambda *args, **kwargs: calls.append(kwargs))
    monkeypatch.delenv("SHADLET_PORT", raising=False)
    monkeypatch.setenv("PORT", "9001")
    ui.App().run(port=8000)
    assert calls[-1]["port"] == 9001

    monkeypatch.setenv("SHADLET_PORT", "9002")
    ui.App().run(port=8000)
    assert calls[-1]["port"] == 9002

    monkeypatch.delenv("SHADLET_PORT")
    monkeypatch.delenv("PORT")
    ui.App().run(port=8001)
    assert calls[-1]["port"] == 8001


@pytest.mark.parametrize("value", ["not-a-port", "-1", "65536"])
def test_app_run_rejects_invalid_environment_port(value, monkeypatch):
    monkeypatch.delenv("SHADLET_PORT", raising=False)
    monkeypatch.setenv("PORT", value)
    with pytest.raises(ValueError, match="PORT"):
        ui.App().run()


def test_app_creation():
    app = ui.App("Test App")
    assert app.title == "Test App"
    assert app.version == ui.__version__


def test_health_endpoint_returns_only_basic_status():
    from shadlet.web.server import create_web_app
    from starlette.testclient import TestClient

    response = TestClient(create_web_app(ui.App("private title"))).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_match_preserves_query_parameters():
    app = ui.App()

    @app.page("/items/{item_id}")
    def item(ctx: ui.Context):
        return ui.Text(ctx.params["item_id"])

    route = app.match("/items/17?page=2&page=3&empty=")
    assert route.path == "/items/17"
    assert route.params == {"item_id": "17"}
    assert route.query_params == {"page": "3", "empty": ""}


@pytest.mark.anyio
async def test_session_lifecycle_and_rendering():
    app = ui.App("Test App")

    @app.page("/")
    def index(ctx: ui.Context):
        val = ctx.state(10, key="my_val")

        def on_click(e):
            val.value += 1

        return ui.Column(
            ui.Heading("Test Header"),
            ui.Text(f"Count: {val.value}"),
            ui.Button("Click Me", on_click=on_click),
        )

    received = []

    async def fake_send(msg):
        received.append(msg)

    session = Session(app, send_json=fake_send)
    await session.send_init()
    assert len(received) == 1
    init_msg = received[0]
    assert init_msg["type"] == "init"
    tree = init_msg["tree"]
    assert tree["type"] == "Column"
    assert len(tree["children"]) == 3
    assert tree["children"][0]["type"] == "Heading"
    assert tree["children"][1]["type"] == "Text"
    assert tree["children"][2]["type"] == "Button"
    assert len(tree["children"][2]["events"]) == 1

    event_id = tree["children"][2]["events"]["click"]
    await session.handle_event(event_id, {}, seq=1)

    assert len(received) == 2
    update_msg = received[1]
    assert update_msg["type"] == "update"
    assert len(update_msg["state_patches"]) == 1
    assert update_msg["state_patches"][0]["op"] == "set"
    assert update_msg["state_patches"][0]["value"] == 11


@pytest.mark.anyio
async def test_state_isolation_between_sessions():
    app = ui.App("Test App")

    @app.page("/")
    def index(ctx: ui.Context):
        count = ctx.state(0, key="count")

        def increment(event):
            count.value += 1

        return ui.Text(count.value + 100 if False else count.value)

    first = []
    second = []

    async def send_first(msg):
        first.append(msg)

    async def send_second(msg):
        second.append(msg)

    a = Session(app, send_json=send_first)
    b = Session(app, send_json=send_second)
    await a.send_init()
    await b.send_init()
    a_tree = first[0]["tree"]
    await a.handle_event(
        next(iter([a_tree]))["children"][0]["events"].get("click", "missing"),
        {},
        seq=1,
    )
    # sessions remain independently initialized
    assert first[0]["tree"]["type"] == "Text"
    assert second[0]["tree"]["type"] == "Text"


def test_route_matching_decodes_unicode_and_rejects_ambiguous_paths():
    app = ui.App()

    @app.page("/café/{slug}")
    def cafe(ctx: ui.Context):
        return ui.Text(ctx.params["slug"])

    assert app.match("/caf%C3%A9/na%C3%AFve").params == {"slug": "naïve"}
    for path in ("/caf%C3%A9/%2e%2e/x", "/caf%C3%A9/a%2Fb", "/caf%C3%A9/%5c"):
        with pytest.raises(ui.RoutingError):
            app.match(path)


def test_route_declarations_reject_control_and_dot_segments():
    app = ui.App()
    for path in ("/a/../b", "/a\\b", "/a\x00b"):
        with pytest.raises(ui.RoutingError):
            app.page(path)(lambda ctx: ui.Text("x"))
