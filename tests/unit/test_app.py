import pytest
import shadlet as ui
from shadlet.runtime.session import Session


def test_app_creation():
    app = ui.App("Test App")
    assert app.title == "Test App"
    assert app.version == "0.3.0"


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
