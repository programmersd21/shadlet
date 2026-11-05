import shadlet as ui

app = ui.App("Server-side data table")

RECORDS = [
    {
        "id": index,
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}@example.test",
        "team": team,
    }
    for index, (first, last, team) in enumerate(
        [
            ("Avery", "Chen", "Design"),
            ("Morgan", "Patel", "Engineering"),
            ("Riley", "Jones", "Support"),
            ("Jordan", "Kim", "Engineering"),
            ("Casey", "Diaz", "Design"),
            ("Taylor", "Singh", "Support"),
            ("Quinn", "Brown", "Engineering"),
            ("Drew", "Wilson", "Design"),
            ("Reese", "Garcia", "Support"),
            ("Jamie", "Martin", "Engineering"),
            ("Skyler", "Lee", "Design"),
            ("Robin", "Clark", "Support"),
        ],
        start=1,
    )
]
PAGE_SIZE = 5


def query_records(query: ui.DataTableQuery) -> tuple[list[dict[str, object]], int]:
    rows = RECORDS
    if query.search:
        needle = query.search.casefold()
        rows = [
            row
            for row in rows
            if needle in str(row["name"]).casefold()
            or needle in str(row["email"]).casefold()
        ]
    team = query.filters.get("team")
    if team:
        rows = [row for row in rows if str(row["team"]).casefold() == team.casefold()]
    if query.sorting:
        sorting = query.sorting[0]
        rows = sorted(
            rows,
            key=lambda row: str(row[sorting.key]).casefold(),
            reverse=sorting.direction == "desc",
        )
    total = len(rows)
    start = query.page_index * query.page_size
    return rows[start : start + query.page_size], total


@app.page("/")
def people(ctx: ui.Context) -> ui.Component:
    rows, total = (
        ctx.state(RECORDS[:PAGE_SIZE], key="people-rows"),
        ctx.state(len(RECORDS), key="people-total"),
    )
    page_index = ctx.state(0, key="people-page")
    search = ctx.state("", key="people-search")
    filters = ctx.state({}, key="people-filters")
    selected = ctx.state([], key="people-selected")

    def query_changed(query: ui.DataTableQuery) -> None:
        current_rows, current_total = query_records(query)
        rows.value = current_rows
        total.value = current_total
        page_index.value = query.page_index
        search.value = query.search
        filters.value = dict(query.filters)

    return ui.Center(
        ui.Column(
            ui.Heading("People", level=1),
            ui.Text(
                "Search and table queries run in Python.",
                variant=ui.TextVariant.MUTED,
            ),
            ui.DataTable(
                [
                    ui.TableColumn("id", "ID", sortable=True),
                    ui.TableColumn("name", "Name", sortable=True),
                    ui.TableColumn("email", "Email", sortable=True),
                    ui.TableColumn("team", "Team", sortable=True, filterable=True),
                ],
                rows.value,
                server_side=True,
                total_rows=total.value,
                page_size=PAGE_SIZE,
                page_index=page_index.value,
                search=search.value,
                filters=filters.value,
                row_key="id",
                selected_keys=selected.value,
                on_selection_change=lambda keys: setattr(selected, "value", keys),
                on_query_change=query_changed,
            ),
            ui.Text(f"Selected rows: {len(selected.value)}"),
            gap=16,
            width="100%",
            max_width=960,
            padding=24,
        ),
        min_height="100vh",
        padding=16,
    )


if __name__ == "__main__":
    app.run()
