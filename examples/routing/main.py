import shadlet as ui

app = ui.App("Routing example")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    return ui.Center(
        ui.Column(
            ui.Heading("Routing in shadlet", level=1),
            ui.Text("Use links for navigation and route parameters for detail pages."),
            ui.Row(
                ui.Link("Open item 42", href="/items/42"),
                ui.Link("Search", href="/search"),
                gap=16,
            ),
            gap=16,
            padding=24,
        ),
        min_height="100vh",
    )


@app.page("/items/{item_id}")
def item_detail(ctx: ui.Context) -> ui.Component:
    item_id = ctx.params["item_id"]
    return ui.Center(
        ui.Column(
            ui.Breadcrumb(
                [
                    ui.BreadcrumbItem("Home", href="/"),
                    ui.BreadcrumbItem(f"Item {item_id}"),
                ]
            ),
            ui.Heading(f"Item {item_id}", level=1),
            ui.Text("Route parameters are decoded and validated by the runtime."),
            ui.Link("Back to home", href="/"),
            gap=16,
            padding=24,
        ),
        min_height="100vh",
    )


@app.page("/search")
def search(ctx: ui.Context) -> ui.Component:
    page = ctx.query_state("page", 1, history="push")

    def next_page(event: ui.ClickEvent) -> None:
        page.value += 1

    def previous_page(event: ui.ClickEvent) -> None:
        page.value = max(1, page.value - 1)

    return ui.Center(
        ui.Column(
            ui.Breadcrumb(
                [ui.BreadcrumbItem("Home", href="/"), ui.BreadcrumbItem("Search")]
            ),
            ui.Heading("Query state", level=1),
            ui.Text(f"Current page: {page.value}"),
            ui.Row(
                ui.Button("Previous", on_click=previous_page, disabled=page.value <= 1),
                ui.Button("Next", on_click=next_page),
                gap=8,
            ),
            ui.Text("Use your browser's back and forward buttons to revisit pages."),
            gap=16,
            padding=24,
        ),
        min_height="100vh",
    )


@app.not_found
def not_found(ctx: ui.Context) -> ui.Component:
    return ui.Center(
        ui.Column(
            ui.Heading("Page not found", level=1),
            ui.Text(f"No page is registered for {ctx.route.path!r}."),
            ui.Link("Return home", href="/"),
            gap=12,
        ),
        min_height="100vh",
        padding=24,
    )


if __name__ == "__main__":
    app.run()
