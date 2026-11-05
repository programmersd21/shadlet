from typing import Any

import pytest
import shadlet as ui
from pydantic import BaseModel, Field, ValidationError
from shadlet.components.base import ComponentError
from shadlet.events.types import Event
from shadlet.runtime.session import Session
from shadlet.state.state import State


def test_button_variants():
    b = ui.Button("x", variant="outline", size="sm")
    assert b.props["variant"] == "outline"
    assert b.props["size"] == "sm"
    with pytest.raises(ComponentError):
        ui.Button("x", variant="nope")


def test_marker_uses_semantic_component_type_and_preserves_children():
    marker = ui.Marker("search result", class_name="custom-highlight")
    assert marker.type == "Marker"
    assert marker.children == ["search result"]
    assert marker.props["className"] == "custom-highlight"


def test_code_block_validates_options_and_serializes_content():
    block = ui.CodeBlock(
        "print('hello')", title="example.py", language="python", line_numbers=True
    )
    assert block.type == "CodeBlock"
    assert block.props["code"] == "print('hello')"
    assert block.props["lineNumbers"] is True
    with pytest.raises(ComponentError, match="code must be a string"):
        ui.CodeBlock(42)  # type: ignore[arg-type]


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
    assert ui.Select(["a"], aria_label="account role").props["ariaLabel"] == (
        "account role"
    )
    assert (
        ui.NativeSelect(["active"], aria_label="account status").props["ariaLabel"]
        == "account status"
    )
    assert (
        ui.RadioGroup(["email"], aria_label="contact preference").props["ariaLabel"]
        == "contact preference"
    )
    assert ui.Combobox(["utc"], aria_label="timezone").props["ariaLabel"] == "timezone"
    assert ui.InputOTP(aria_label="verification code").props["ariaLabel"] == (
        "verification code"
    )
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


def test_data_table_selection_requires_stable_row_keys_and_validates_keys():
    selected: list[list[str]] = []
    table = ui.DataTable(
        [{"key": "name", "header": "name"}],
        [{"id": 1, "name": "Ruby"}, {"id": 2, "name": "Python"}],
        row_key="id",
        selected_keys=[1],
        on_selection_change=selected.append,
    )
    assert table.props["selectedKeys"] == ["1"]
    table.events["selection_change"](
        Event(
            name="selection_change",
            node_id="table",
            route="/",
            values={"keys": ["1", "2"]},
        )
    )
    assert selected == [["1", "2"]]

    with pytest.raises(ComponentError, match="row_key is required"):
        ui.DataTable(
            [{"key": "name", "header": "name"}],
            [{"name": "Ruby"}],
            on_selection_change=selected.append,
        )

    invalid = ui.DataTable(
        [{"key": "name", "header": "name"}],
        [{"id": 1, "name": "Ruby"}],
        row_key="id",
        on_selection_change=selected.append,
    )
    with pytest.raises(ComponentError, match="must be unique"):
        invalid.events["selection_change"](
            Event(
                name="selection_change",
                node_id="table",
                route="/",
                values={"keys": ["1", "1"]},
            )
        )


def test_new_table_query_cancels_pending_async_query():
    import asyncio

    started = asyncio.Event()
    cancelled = asyncio.Event()
    ctx_rows = [{"name": "initial"}]
    completed: list[str] = []
    app = ui.App("cancel queries")

    @app.page("/")
    def home(ctx: ui.Context):
        state_rows = ctx.state(ctx_rows, key="cancel-query-rows")

        async def query_changed(query: ui.DataTableQuery):
            if query.search == "slow":
                started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    raise
            else:
                state_rows.value = [{"name": query.search}]
                completed.append(query.search)

        return ui.DataTable(
            [{"key": "name", "header": "name"}],
            state_rows.value,
            server_side=True,
            total_rows=1,
            on_query_change=query_changed,
        )

    messages: list[dict] = []

    async def send(message):
        messages.append(message)

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        event_id = messages[0]["tree"]["events"]["query_change"]
        slow = {
            "values": {
                "page_index": 0,
                "page_size": 10,
                "sorting": [],
                "search": "slow",
                "filters": {},
            }
        }
        fast = {**slow, "values": {**slow["values"], "search": "fast"}}
        await session.handle_event(event_id, slow, seq=1)
        await started.wait()
        await session.handle_event(event_id, fast, seq=2)
        await asyncio.sleep(0)
        assert cancelled.is_set()
        assert completed == ["fast"]
        assert messages[-1]["type"] == "update"
        assert messages[-1]["patches"]
        await session.close()

    asyncio.run(exercise())


def test_pydantic_form_preserves_multiple_errors_for_one_field(monkeypatch):
    class Signup(BaseModel):
        username: str

    error = ValidationError.from_exception_data(
        "Signup",
        [
            {
                "type": "value_error",
                "loc": ("username",),
                "input": "x",
                "ctx": {"error": ValueError("too short")},
            },
            {
                "type": "value_error",
                "loc": ("username",),
                "input": "x",
                "ctx": {"error": ValueError("invalid characters")},
            },
        ],
    )

    def reject(cls, values):
        raise error

    monkeypatch.setattr(Signup, "model_validate", classmethod(reject))
    field_errors: State[dict[str, str]] = State(
        {}, key="field-errors", on_change=lambda key: None
    )
    form = ui.pydantic_form(
        Signup,
        ui.Input(name="username"),
        on_submit=lambda value: None,
        field_errors=field_errors,
    )

    form.events["submit"](
        Event(
            name="submit",
            node_id="form",
            route="/",
            values={"username": "x"},
        )
    )
    assert field_errors.value["username"] == (
        "Value error, too short; Value error, invalid characters"
    )


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


@pytest.mark.parametrize("page_size", [0, 501, True, 10.5])
def test_data_table_page_size_matches_query_protocol_limit(page_size):
    with pytest.raises(ComponentError, match="integer from 1 to 500"):
        ui.DataTable(
            [{"key": "name", "header": "name"}],
            [],
            server_side=True,
            total_rows=0,
            page_size=page_size,
            on_query_change=lambda query: None,
        )


def test_data_table_accepts_maximum_server_query_page_size():
    table = ui.DataTable(
        [{"key": "name", "header": "name"}],
        [],
        server_side=True,
        total_rows=0,
        page_size=500,
        on_query_change=lambda query: None,
    )
    assert table.props["pageSize"] == 500


def test_box_supports_semantic_fragment_targets():
    section = ui.Box(ui.Heading("Pricing"), as_="section", id="pricing")
    assert section.props["id"] == "pricing"
    assert section.props["as"] == "section"
    assert ui.Text("text", as_="span").props["as"] == "span"
    assert ui.Grid(id="features", as_="section").props["as"] == "section"
    with pytest.raises(ComponentError, match="id must be a non-empty string"):
        ui.Box(id=" ")


def test_data_table_exposes_loading_error_and_retry_state():
    retried: list[Any] = []
    table = ui.DataTable(
        [{"key": "name", "header": "name"}],
        [{"name": "stale row"}],
        loading=True,
        error="request failed",
        on_retry=retried.append,
    )
    assert table.props["loading"] is True
    assert table.props["error"] == "request failed"
    assert "retry" in table.events

    invalid_loading: Any = "yes"
    with pytest.raises(ComponentError, match="loading must be a boolean"):
        ui.DataTable([{"key": "name", "header": "name"}], [], loading=invalid_loading)


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([{"id": 1}, {"id": 1}], "non-empty and unique"),
        ([{"name": "missing"}], "missing the row_key field"),
        ([{"id": True}], "invalid value for row_key"),
    ],
)
def test_data_table_validates_stable_row_keys(rows, message):
    with pytest.raises(ComponentError, match=message):
        ui.DataTable([{"key": "name", "header": "name"}], rows, row_key="id")


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


def test_closed_session_rejects_background_tasks_without_mutating_state():
    import asyncio

    app = ui.App("closed task session")
    contexts: list[ui.Context] = []

    @app.page("/")
    def home(ctx: ui.Context):
        contexts.append(ctx)
        task_state = ctx.task_state("worker")
        return ui.Text(task_state.value["status"])

    async def send(message):
        return None

    async def worker(task):
        return None

    session = Session(app, send_json=send)

    async def exercise():
        await session.send_init()
        await session.close()
        with pytest.raises(RuntimeError, match="closed session"):
            contexts[0].start_task("worker", worker, key="worker")
        assert session.state_store.snapshot()["/:task:worker"]["status"] == "idle"
        assert session._tasks == set()

    asyncio.run(exercise())
