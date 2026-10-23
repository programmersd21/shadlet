import shadlet as ui

app = ui.App("my app")


@app.page("/")
def home(ctx: ui.Context):
    count = ctx.state(0, key="count")

    def increment(event: ui.ClickEvent):
        count.value += 1

    return ui.Center(
        ui.Column(
            ui.Heading("hello shadlet"),
            ui.Text(count),
            ui.Button("increment", on_click=increment),
            gap=16,
        ),
        min_height="100vh",
    )


if __name__ == "__main__":
    app.run()
