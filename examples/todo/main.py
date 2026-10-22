import shadlet as ui

app = ui.App("todo")


@app.page("/")
def home(ctx: ui.Context):
    items = ctx.state(["buy milk", "write docs"], key="items")
    draft = ctx.state("", key="draft")

    def add(event: ui.SubmitEvent):
        text = str(draft.value).strip()
        if text:
            items.value = [*items.value, text]
            draft.value = ""

    def remove(index: int):
        def handler(event: ui.ClickEvent):
            items.value = [v for i, v in enumerate(items.value) if i != index]

        return handler

    return ui.Center(
        ui.Column(
            ui.Heading("todo"),
            ui.Form(
                ui.Row(
                    ui.Input(
                        value=draft,
                        on_change=lambda e: setattr(draft, "value", e.value),
                        placeholder="new task",
                    ),
                    ui.Button("add", type="submit"),
                    gap=8,
                ),
                on_submit=add,
            ),
            ui.Column(
                *[
                    ui.Row(
                        ui.Text(task),
                        ui.Button(
                            "remove", variant=ui.ButtonVariant.GHOST, on_click=remove(i)
                        ),
                        justify=ui.Justify.BETWEEN,
                        gap=8,
                    )
                    for i, task in enumerate(items.value)
                ],
                gap=4,
            ),
            gap=16,
            max_width=480,
        ),
        min_height="100vh",
        padding=24,
    )


if __name__ == "__main__":
    app.run()
