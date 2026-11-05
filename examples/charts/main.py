import shadlet as ui

app = ui.App("Charts")

MONTHS = [
    {"name": "Jan", "sales": 34, "returns": 4, "share": 18, "score": 7},
    {"name": "Feb", "sales": 48, "returns": 6, "share": 22, "score": 8},
    {"name": "Mar", "sales": 41, "returns": 5, "share": 19, "score": 6},
    {"name": "Apr", "sales": 62, "returns": 7, "share": 26, "score": 9},
]
SERIES = [ui.ChartSeries("sales", "Sales"), ui.ChartSeries("returns", "Returns")]


def chart_card(title: str, kind: ui.ChartKind) -> ui.Component:
    return ui.Card(
        title=title,
        children=ui.Chart(
            data=MONTHS,
            series=SERIES if kind != ui.ChartKind.PIE else [SERIES[0]],
            kind=kind,
            height=260,
        ),
    )


@app.page("/")
def overview(ctx: ui.Context) -> ui.Component:
    return ui.Column(
        ui.Row(
            ui.Column(
                ui.Heading("Charts", level=1),
                ui.Text("Responsive visualizations with application-owned data."),
                gap=4,
            ),
            ui.ThemeToggle(),
            justify=ui.Justify.BETWEEN,
            align=ui.Align.CENTER,
        ),
        ui.Grid(
            chart_card("Monthly sales", ui.ChartKind.BAR),
            chart_card("Trend", ui.ChartKind.LINE),
            chart_card("Area", ui.ChartKind.AREA),
            chart_card("Share", ui.ChartKind.PIE),
            chart_card("Radar", ui.ChartKind.RADAR),
            ui.Card(
                title="No data yet",
                children=ui.Empty(
                    title="Nothing to chart",
                    description="Connect a data source to show a visualization.",
                ),
            ),
            columns=ui.Responsive(base=1, md=2, xl=3),
            gap=16,
        ),
        gap=24,
        width="100%",
        max_width=1280,
        padding=24,
        margin=(0, "auto"),
    )


if __name__ == "__main__":
    app.run()
