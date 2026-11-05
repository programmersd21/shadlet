from pathlib import Path

import shadlet as ui


class ExtensionNotice(ui.Component):
    type = "browser_fixture:Notice"

    def __init__(self) -> None:
        super().__init__(message="extension ready")


class FragileNotice(ui.Component):
    type = "browser_fixture:Fragile"

    def __init__(self, ready: bool) -> None:
        super().__init__(ready=ready)


app = ui.App("browser test")
app.add_extension(
    ui.ExtensionManifest(
        name="browser_fixture",
        version="1.0.0",
        assets=Path(__file__).parent / "extension_assets",
        stylesheet="index.css",
    )
)


@app.page("/")
def home(ctx: ui.Context):
    count = ctx.state(0, key="count")
    page = ctx.query_state("page", 1, history="push")
    users = [
        {"name": "Ruby"},
        {"name": "Python"},
        {"name": "Rust"},
    ]
    table_rows = ctx.state(users[:2], key="table-rows")
    table_total = ctx.state(len(users), key="table-total")
    table_search = ctx.state("", key="table-search")

    def increment(event: ui.ClickEvent) -> None:
        count.value += 1

    def next_page(event: ui.ClickEvent) -> None:
        page.value += 1

    def filter_users(query: ui.DataTableQuery) -> None:
        matching = [
            row for row in users if query.search.casefold() in row["name"].casefold()
        ]
        table_search.value = query.search
        table_total.value = len(matching)
        table_rows.value = matching[: query.page_size]

    return ui.Column(
        ui.Text(f"count: {count.value}"),
        ui.Button("increment", on_click=increment),
        ui.Text(f"page: {page.value}"),
        ui.Button("next page", on_click=next_page),
        ExtensionNotice(),
        ui.DataTable(
            [{"key": "name", "header": "name"}],
            table_rows.value,
            server_side=True,
            total_rows=table_total.value,
            page_size=2,
            search=table_search.value,
            on_query_change=filter_users,
        ),
    )


@app.page("/icons")
def icons_page(ctx: ui.Context):
    return ui.Column(
        ui.Icon("arrow-up-right", size=20, label="open link"),
        ui.icons.house(size=18, label="home icon"),
        ui.Button("save", icon="check"),
    )


@app.page("/recovery")
def recovery_page(ctx: ui.Context):
    ready = ctx.state(False, key="ready")

    def make_ready(event: ui.ClickEvent) -> None:
        ready.value = True

    return ui.Column(
        ui.Button("make ready", on_click=make_ready),
        FragileNotice(ready.value),
    )


@app.page("/accessibility")
def accessibility_page(ctx: ui.Context):
    return ui.Column(
        ui.Heading("accessibility test page", level=1),
        ui.Field(ui.Input(type="email"), label="email address"),
        ui.Field(ui.Textarea(), label="profile biography"),
        ui.Checkbox(label="receive updates"),
        ui.Switch(label="enable notifications"),
        ui.Slider(aria_label="volume"),
        ui.Select(["member"], aria_label="account role"),
        ui.NativeSelect(["active"], aria_label="account status"),
        ui.RadioGroup(["email"], aria_label="contact preference"),
        ui.Combobox(["utc"], aria_label="timezone"),
        ui.InputOTP(aria_label="verification code"),
        ui.Button("save settings"),
        ui.Alert(title="saved", description="settings were updated"),
        ui.Progress(value=50, label="upload progress"),
        ui.DataTable(
            [{"key": "name", "header": "name"}],
            [{"id": 1, "name": "Ruby"}],
            row_key="id",
            on_selection_change=lambda keys: None,
            on_row_click=lambda event: None,
        ),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
