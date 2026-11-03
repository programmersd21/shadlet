from pathlib import Path

import shadlet as ui


class ExtensionNotice(ui.Component):
    type = "browser_fixture:Notice"

    def __init__(self) -> None:
        super().__init__(message="extension ready")


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

    def increment(event: ui.ClickEvent) -> None:
        count.value += 1

    def next_page(event: ui.ClickEvent) -> None:
        page.value += 1

    return ui.Column(
        ui.Text(f"count: {count.value}"),
        ui.Button("increment", on_click=increment),
        ui.Text(f"page: {page.value}"),
        ui.Button("next page", on_click=next_page),
        ExtensionNotice(),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
