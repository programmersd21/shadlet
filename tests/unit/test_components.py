import pytest
import shadlet as ui
from pydantic import BaseModel, Field
from shadlet.components.base import ComponentError
from shadlet.runtime.session import Session
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


def test_server_side_data_table_validates_and_delivers_query():
    received: list[ui.DataTableQuery] = []
    app = ui.App("table")

    @app.page("/")
    def home(ctx: ui.Context):
        return ui.DataTable(
            [{"key": "name", "header": "name", "sortable": True}],
            [{"name": "first"}],
            server_side=True,
            total_rows=10_000,
            page_size=25,
            on_query_change=received.append,
        )

    messages: list[dict] = []

    async def send(message):
        messages.append(message)

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        node = messages[0]["tree"]
        assert node["props"]["totalRows"] == 10_000
        assert len(node["props"]["rows"]) == 1
        event_id = node["events"]["query_change"]
        await session.handle_event(
            event_id,
            {
                "values": {
                    "page_index": 1,
                    "page_size": 25,
                    "sorting": [{"key": "name", "direction": "desc"}],
                    "search": "first",
                    "filters": {},
                }
            },
            seq=1,
        )
        assert received == [
            ui.DataTableQuery(
                page_index=1,
                page_size=25,
                sorting=[ui.DataTableSort(key="name", direction="desc")],
                search="first",
                filters={},
            )
        ]
        await session.handle_event(
            event_id,
            {
                "values": {
                    "page_index": 0,
                    "page_size": 25,
                    "sorting": [{"key": "other", "direction": "asc"}],
                    "search": "",
                    "filters": {},
                }
            },
            seq=2,
        )
        assert messages[-1]["type"] == "error"
        assert received == [
            ui.DataTableQuery(
                page_index=1,
                page_size=25,
                sorting=[ui.DataTableSort(key="name", direction="desc")],
                search="first",
                filters={},
            )
        ]

    import asyncio

    asyncio.run(exercise())


def test_server_side_data_table_rejects_unknown_sort_key():
    with pytest.raises(ComponentError, match="sortable columns"):
        ui.DataTable(
            [{"key": "name", "header": "name", "sortable": True}],
            [],
            server_side=True,
            total_rows=0,
            sorting=[{"key": "other", "direction": "asc"}],
            on_query_change=lambda query: None,
        )


def test_pydantic_form_validates_submission_and_field_errors():
    import asyncio

    class Signup(BaseModel):
        username: str = Field(min_length=3)
        age: int = Field(ge=13)

    submitted: list[Signup] = []
    app = ui.App("form")

    @app.page("/")
    def home(ctx: ui.Context):
        errors = ctx.state({}, key="field-errors")
        form_error = ctx.state("", key="form-error")

        async def submit(values: Signup):
            await asyncio.sleep(0)
            submitted.append(values)

        return ui.pydantic_form(
            Signup,
            ui.Input(name="username"),
            ui.Input(name="age"),
            on_submit=submit,
            field_errors=errors,
            form_error=form_error,
        )

    messages: list[dict] = []

    async def send(message):
        messages.append(message)

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        event_id = messages[0]["tree"]["events"]["submit"]
        await session.handle_event(
            event_id,
            {"values": {"username": "ab", "age": "11"}},
            seq=1,
        )
        snapshot = session.state_store.snapshot()
        assert snapshot["/:field-errors"]["username"]
        assert snapshot["/:field-errors"]["age"]
        assert snapshot["/:form-error"]
        assert not submitted

        await session.handle_event(
            event_id,
            {"values": {"username": "alice", "age": "20"}},
            seq=2,
        )
        assert submitted == [Signup(username="alice", age=20)]
        assert session.state_store.snapshot()["/:field-errors"] == {}

    asyncio.run(exercise())


def test_context_background_task_updates_reactive_state():
    import asyncio

    app = ui.App("task")

    @app.page("/")
    def home(ctx: ui.Context):
        state = ctx.task_state("report", label="report")

        async def run_report(task):
            await task.update(progress=40, message="working")
            await asyncio.sleep(0)
            await task.update(progress=90)

        async def start(event):
            ctx.start_task("report", run_report, key="report")

        return ui.Column(
            ui.Text(state.value["status"]),
            ui.Progress(value=state.value["progress"]),
            ui.Button("start", on_click=start),
        )

    messages: list[dict] = []

    async def send(message):
        messages.append(message)

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        event_id = messages[0]["tree"]["children"][2]["events"]["click"]
        await session.handle_event(event_id, {}, seq=1)
        for _ in range(20):
            if session.state_store.snapshot()["/:task:report"]["status"] == "completed":
                break
            await asyncio.sleep(0)
        assert session.state_store.snapshot()["/:task:report"]["status"] == "completed"
        assert session.state_store.snapshot()["/:task:report"]["progress"] == 100
        await session.close()

    asyncio.run(exercise())


def test_context_background_task_can_be_cancelled():
    import asyncio

    app = ui.App("task cancellation")
    task_handles: list[ui.BackgroundTask] = []
    wait_forever = asyncio.Event()

    @app.page("/")
    def home(ctx: ui.Context):
        state = ctx.task_state("worker")

        async def worker(task):
            await wait_forever.wait()

        async def start(event):
            task_handles.append(ctx.start_task("worker", worker, key="worker"))

        return ui.Column(
            ui.Text(state.value["status"]), ui.Button("start", on_click=start)
        )

    messages: list[dict] = []

    async def send(message):
        messages.append(message)

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        event_id = messages[0]["tree"]["children"][1]["events"]["click"]
        await session.handle_event(event_id, {}, seq=1)
        await task_handles[0].cancel()
        assert session.state_store.snapshot()["/:task:worker"]["status"] == "cancelled"
        await session.close()

    asyncio.run(exercise())
