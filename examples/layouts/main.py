import shadlet as ui

app = ui.App("Layouts and themes")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    cards = [
        ui.Card(
            title=f"Workspace {index}",
            description="A responsive card in a CSS grid.",
            children=ui.Link("View details", href="#details"),
        )
        for index in range(1, 7)
    ]
    return ui.Column(
        ui.Box(
            ui.Row(
                ui.Link("shadlet layouts", href="#top"),
                ui.Row(
                    ui.Link("Workspaces", href="#workspaces"),
                    ui.Link("Details", href="#details"),
                    ui.ThemeToggle(),
                    align=ui.Align.CENTER,
                    gap=16,
                ),
                justify=ui.Justify.BETWEEN,
                align=ui.Align.CENTER,
                width="100%",
                max_width=1200,
                margin=(0, "auto"),
                padding=(12, 24),
            ),
            as_="header",
            id="top",
            class_name="sticky top-0 z-10 border-b bg-background/95 backdrop-blur",
        ),
        ui.Box(
            ui.Column(
                ui.Badge("Layout primitives", variant=ui.BadgeVariant.SECONDARY),
                ui.Heading("Build responsive pages in Python", level=1),
                ui.Text(
                    "Use Row, Column, Grid, Container, and semantic Box tags to compose an application shell."
                ),
                ui.Link("Browse workspaces", href="#workspaces"),
                gap=16,
            ),
            as_="main",
            width="100%",
            max_width=1200,
            margin=(0, "auto"),
            padding=24,
            class_name="py-16 sm:py-24",
        ),
        ui.Box(
            ui.Column(
                ui.Heading("Workspaces", level=2),
                ui.Grid(
                    *cards,
                    columns=ui.Responsive(base=1, sm=2, lg=3),
                    gap=16,
                ),
                gap=16,
            ),
            as_="section",
            id="workspaces",
            width="100%",
            max_width=1200,
            margin=(0, "auto"),
            padding=24,
        ),
        ui.Box(
            ui.Column(
                ui.Heading("Semantic targets", level=2),
                ui.Text("The header links jump to section IDs rendered by Box."),
            ),
            as_="section",
            id="details",
            width="100%",
            max_width=1200,
            margin=(0, "auto"),
            padding=24,
            class_name="border-t",
        ),
        ui.Box(
            ui.Text("Layout example · shadlet", variant=ui.TextVariant.MUTED),
            as_="footer",
            padding=24,
            class_name="border-t",
        ),
        gap=0,
        min_height="100vh",
    )


if __name__ == "__main__":
    app.run()
