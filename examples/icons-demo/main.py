import shadlet as ui

app = ui.App("Icon Demo")


@app.page("/")
def home(ctx: ui.Context):
    count = ctx.state(0, key="count")

    def increment(event: ui.ClickEvent) -> None:
        count.value += 1

    return ui.Column(
        ui.Heading("Icon Demo", level=1),
        ui.Icon("arrow-up-right", size=24, label="increment"),
        ui.icons.arrow_up_right(size=20, label="icon namespace"),
        ui.Button("Click Me", icon="check", on_click=increment),
        ui.Button("Save", icon="save", loading=False),
        ui.Text(f"Count: {count.value}"),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
