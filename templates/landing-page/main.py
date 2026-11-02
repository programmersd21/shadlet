import shadlet as ui

app = ui.App("landing")


@app.page("/")
def home(ctx: ui.Context):
    return ui.Column(
        ui.Container(
            ui.Row(
                ui.Heading("shadlet", level=1),
                ui.Button("get started", variant=ui.ButtonVariant.DEFAULT),
                justify=ui.Justify.BETWEEN,
                align=ui.Align.CENTER,
            ),
            ui.Heading("python-first web apps", level=2),
            ui.Text("build with genuine shadcn/ui", variant=ui.TextVariant.MUTED),
            ui.Grid(
                ui.Card(title="fast", description="python backend, react frontend"),
                ui.Card(title="typed", description="pydantic + typescript"),
                ui.Card(title="reactive", description="session-scoped state"),
                columns=ui.Responsive(base=1, md=3),
                gap=16,
            ),
            max_width=1100,
            padding=32,
        ),
        gap=0,
    )


if __name__ == "__main__":
    app.run()
