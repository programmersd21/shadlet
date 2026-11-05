import shadlet as ui

app = ui.App("{{ title }}")


def render_sidebar(current_path: str):
    return ui.Sidebar(
        sections=[
            ui.SidebarSection(
                label="overview",
                items=[
                    ui.SidebarItem(
                        label="dashboard", href="/", active=(current_path == "/")
                    ),
                    ui.SidebarItem(
                        label="analytics",
                        href="/analytics",
                        active=(current_path == "/analytics"),
                    ),
                    ui.SidebarItem(
                        label="settings",
                        href="/settings",
                        active=(current_path == "/settings"),
                    ),
                ],
            )
        ]
    )


def page_shell(current_path: str, title: str, content: ui.Component):
    return ui.Row(
        render_sidebar(current_path),
        ui.Column(
            ui.Row(
                ui.Heading(title, level=2),
                ui.ThemeToggle(),
                justify=ui.Justify.BETWEEN,
                align=ui.Align.CENTER,
            ),
            content,
            gap=16,
            padding=24,
            width="100%",
            max_width=900,
            margin=(0, "auto"),
        ),
        gap=0,
        width="100%",
        min_height="100vh",
    )


@app.page("/")
def home(ctx: ui.Context):
    content = ui.Column(
        ui.Grid(
            ui.Card(title="revenue", description="$12,400", children=ui.Text("+12%")),
            ui.Card(title="users", description="1,204", children=ui.Text("+5%")),
            ui.Card(title="orders", description="320", children=ui.Text("-2%")),
            columns=ui.Responsive(base=1, md=3),
            gap=16,
        ),
        ui.Card(
            title="traffic",
            children=ui.Chart(
                data=[
                    {"name": "mon", "visits": 120},
                    {"name": "tue", "visits": 200},
                    {"name": "wed", "visits": 150},
                    {"name": "thu", "visits": 280},
                    {"name": "fri", "visits": 220},
                ],
                series=[ui.ChartSeries(key="visits", label="visits")],
                kind=ui.ChartKind.BAR,
                height=260,
            ),
        ),
        ui.Card(
            title="recent orders",
            children=ui.DataTable(
                columns=[
                    ui.TableColumn(key="id", header="id"),
                    ui.TableColumn(key="customer", header="customer"),
                    ui.TableColumn(key="total", header="total", align="right"),
                ],
                rows=[
                    {"id": "1001", "customer": "alice", "total": "$42"},
                    {"id": "1002", "customer": "bob", "total": "$18"},
                    {"id": "1003", "customer": "carol", "total": "$99"},
                ],
                page_size=5,
            ),
        ),
        gap=16,
    )
    return page_shell("/", "dashboard", content)


@app.page("/analytics")
def analytics(ctx: ui.Context):
    content = ui.Column(
        ui.Grid(
            ui.Card(
                title="bounce rate",
                description="24.8%",
                children=ui.Text("-3.2% vs last month"),
            ),
            ui.Card(
                title="session duration",
                description="4m 12s",
                children=ui.Text("+45s vs last month"),
            ),
            ui.Card(
                title="conversion rate", description="3.6%", children=ui.Text("+0.8%")
            ),
            columns=ui.Responsive(base=1, md=3),
            gap=16,
        ),
        ui.Card(
            title="page views & retention",
            children=ui.Chart(
                data=[
                    {"name": "week 1", "views": 1200},
                    {"name": "week 2", "views": 1850},
                    {"name": "week 3", "views": 2400},
                    {"name": "week 4", "views": 3100},
                ],
                series=[ui.ChartSeries(key="views", label="views")],
                kind=ui.ChartKind.LINE,
                height=280,
            ),
        ),
        gap=16,
    )
    return page_shell("/analytics", "analytics", content)


@app.page("/settings")
def settings(ctx: ui.Context):
    app_name = ctx.state("My Dashboard", key="app_name")
    notifications = ctx.state(True, key="notifications")

    content = ui.Column(
        ui.Card(
            title="general settings",
            description="manage application configuration",
            children=ui.Column(
                ui.Row(
                    ui.Text("app name"),
                    ui.Input(
                        value=app_name,
                        on_change=lambda e: setattr(app_name, "value", e.value),
                    ),
                    align=ui.Align.CENTER,
                    justify=ui.Justify.BETWEEN,
                    gap=16,
                ),
                ui.Row(
                    ui.Text("enable notifications"),
                    ui.Switch(
                        checked=notifications,
                        on_change=lambda e: setattr(notifications, "value", e.value),
                    ),
                    align=ui.Align.CENTER,
                    justify=ui.Justify.BETWEEN,
                    gap=16,
                ),
                gap=16,
            ),
        ),
        gap=16,
    )
    return page_shell("/settings", "settings", content)


if __name__ == "__main__":
    app.run()
