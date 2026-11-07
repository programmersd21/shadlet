"""Flagship document workspace example for Shadlet 0.8.0."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any

import shadlet as ui

sys.path.insert(0, str(Path(__file__).resolve().parent))
from database import Database, DatabaseError
from models import REVIEWERS, SECTION_TYPES, STATUSES

db = Database()
db.initialize()

PAGE_SIZE = 10
CHART_RANGES = {"7d": 7, "30d": 30, "3m": 90}


def _initial_table() -> tuple[list[dict[str, Any]], int]:
    try:
        return db.list_sections(offset=0, limit=PAGE_SIZE)
    except DatabaseError:
        return [], 0


def _sidebar(path: str) -> ui.Component:
    def item(label: str, href: str) -> ui.SidebarItem:
        return ui.SidebarItem(label=label, href=href, active=(path == href))

    return ui.Sidebar(
        sections=[
            ui.SidebarSection(
                label="workspace",
                items=[
                    item("Home", "/"),
                    item("Dashboard", "/dashboard"),
                    item("Lifecycle", "/lifecycle"),
                    item("Analytics", "/analytics"),
                    item("Projects", "/projects"),
                    item("Team", "/team"),
                ],
            ),
            ui.SidebarSection(
                label="library",
                items=[
                    item("Data Library", "/data-library"),
                    item("Reports", "/reports"),
                    item("Word Assistant", "/word-assistant"),
                ],
            ),
            ui.SidebarSection(
                label="system",
                items=[
                    item("More", "/more"),
                    item("Settings", "/settings"),
                    item("Get Help", "/help"),
                    item("Search", "/search"),
                ],
            ),
        ],
        header=ui.Column(
            ui.Text("Acme Inc", variant=ui.TextVariant.LARGE, class_name="truncate"),
            ui.Text(
                "Enterprise workspace",
                variant=ui.TextVariant.MUTED,
                class_name="truncate",
            ),
            gap=2,
            class_name="min-w-0",
        ),
        footer=ui.ThemeToggle(),
        collapsible="icon",
    )


def _kpi_cards() -> ui.Component:
    cards = [
        ("Total Revenue", "$1,250.00", "+12.5%", "Revenue from all document projects"),
        ("New Customers", "1,234", "+8.2%", "Customers added this quarter"),
        ("Active Accounts", "45,678", "+3.1%", "Accounts with recent activity"),
        ("Growth Rate", "4.5%", "+1.2%", "Year-over-year workspace growth"),
    ]
    return ui.Grid(
        *[
            ui.Card(
                title=title,
                description=value,
                children=ui.Row(
                    ui.Badge(change, variant=ui.BadgeVariant.SECONDARY),
                    ui.Text(description, variant=ui.TextVariant.MUTED),
                    gap=8,
                    align=ui.Align.CENTER,
                ),
            )
            for title, value, change, description in cards
        ],
        columns=ui.Responsive(base=1, sm=2, xl=4),
        gap=16,
    )


def _chart_data(range_key: str) -> list[dict[str, Any]]:
    days = CHART_RANGES[range_key]
    today = dt.date.today()
    data: list[dict[str, Any]] = []
    for offset in range(days - 1, -1, -1):
        day = today - dt.timedelta(days=offset)
        seed = (day.toordinal() * 37) % 100
        data.append(
            {
                "date": day.strftime("%b %d"),
                "mobile": 40 + seed % 45,
                "desktop": 70 + (seed * 2) % 60,
            }
        )
    return data


def _table_query(
    query: ui.DataTableQuery,
    rows_state: ui.State,
    total_state: ui.State,
    page_state: ui.State,
    search_state: ui.State,
    filters_state: ui.State,
    sorting_state: ui.State,
) -> None:
    sort_key = "name"
    sort_direction = "asc"
    if query.sorting:
        sort_key = query.sorting[0].key
        sort_direction = query.sorting[0].direction
    try:
        rows, total = db.list_sections(
            search=query.search,
            status=query.filters.get("status"),
            section_type=query.filters.get("section_type"),
            sort_key=sort_key,
            sort_direction=sort_direction,
            offset=query.page_index * query.page_size,
            limit=query.page_size,
        )
    except DatabaseError:
        rows, total = [], 0
    rows_state.value = rows
    total_state.value = total
    page_state.value = query.page_index
    search_state.value = query.search
    filters_state.value = dict(query.filters)
    sorting_state.value = [
        {"id": item.key, "desc": item.direction == "desc"} for item in query.sorting
    ]


def _page_content(path: str, ctx: ui.Context) -> ui.Component:
    if path in {"/", "/dashboard", "/lifecycle"}:
        initial_rows, initial_total = _initial_table()
        rows_state = ctx.state(initial_rows, key="section-rows")
        total_state = ctx.state(initial_total, key="section-total")
        page_state = ctx.state(0, key="section-page")
        search_state = ctx.state("", key="section-search")
        filters_state = ctx.state({}, key="section-filters")
        sorting_state = ctx.state([], key="section-sorting")
        selected_state = ctx.state([], key="section-selected")
        create_name = ctx.state("", key="create-name")
        create_type = ctx.state(SECTION_TYPES[0], key="create-type")
        create_status = ctx.state(STATUSES[0], key="create-status")
        create_target = ctx.state("100", key="create-target")
        create_limit = ctx.state("20", key="create-limit")
        create_reviewer = ctx.state(REVIEWERS[0], key="create-reviewer")
        quick_open = ctx.state(False, key="quick-open")
        edit_open = ctx.state(False, key="edit-open")
        edit_id = ctx.state(None, key="edit-id")
        edit_name = ctx.state("", key="edit-name")
        edit_type = ctx.state(SECTION_TYPES[0], key="edit-type")
        edit_status = ctx.state(STATUSES[0], key="edit-status")
        edit_target = ctx.state(100, key="edit-target")
        edit_limit = ctx.state(20, key="edit-limit")
        edit_reviewer = ctx.state(REVIEWERS[0], key="edit-reviewer")
        range_state = ctx.state("30d", key="chart-range")
        tab_state = ctx.state("outline", key="document-tab")

        def query_changed(query: ui.DataTableQuery) -> None:
            _table_query(
                query,
                rows_state,
                total_state,
                page_state,
                search_state,
                filters_state,
                sorting_state,
            )

        def open_create(event: ui.ClickEvent) -> None:
            quick_open.value = True

        def submit_create(event: ui.SubmitEvent) -> None:
            values = event.values
            try:
                db.create_section(
                    {
                        "name": values.get("name") or "Untitled section",
                        "section_type": values.get("section_type") or SECTION_TYPES[0],
                        "status": values.get("status") or STATUSES[0],
                        "target": int(values.get("target") or 100),
                        "limit": int(values.get("limit") or 20),
                        "reviewer": values.get("reviewer") or REVIEWERS[0],
                    }
                )
                ctx.toast("Section created", level=ui.ToastLevel.SUCCESS)
            except (DatabaseError, ValueError, TypeError):
                ctx.toast("Could not create section", level=ui.ToastLevel.ERROR)
            quick_open.value = False
            rows, total = db.list_sections(
                search=search_state.value,
                status=filters_state.value.get("status"),
                section_type=filters_state.value.get("section_type"),
                offset=page_state.value * PAGE_SIZE,
                limit=PAGE_SIZE,
            )
            rows_state.value = rows
            total_state.value = total

        def open_edit(event: ui.ClickEvent) -> None:
            section_id = (
                event.value.get("id") if isinstance(event.value, dict) else None
            )
            if section_id is None:
                return
            section = db.get_section(int(section_id))
            if section is None:
                return
            edit_id.value = int(str(section["id"]))
            edit_name.value = str(section["name"])
            edit_type.value = str(section["section_type"])
            edit_status.value = str(section["status"])
            edit_target.value = int(str(section["target"]))
            edit_limit.value = int(str(section["limit_value"]))
            edit_reviewer.value = str(section["reviewer"])
            edit_open.value = True

        def submit_edit(event: ui.SubmitEvent) -> None:
            if edit_id.value is None:
                return
            values = event.values
            try:
                db.update_section(
                    int(edit_id.value),
                    {
                        "name": values.get("name") or edit_name.value,
                        "section_type": values.get("section_type") or edit_type.value,
                        "status": values.get("status") or edit_status.value,
                        "target": int(values.get("target") or edit_target.value),
                        "limit": int(values.get("limit") or edit_limit.value),
                        "reviewer": values.get("reviewer") or edit_reviewer.value,
                    },
                )
                ctx.toast("Section updated", level=ui.ToastLevel.SUCCESS)
            except (DatabaseError, ValueError, TypeError):
                ctx.toast("Could not update section", level=ui.ToastLevel.ERROR)
            edit_open.value = False

        def delete_selected(event: ui.ClickEvent) -> None:
            ids = [int(key) for key in selected_state.value if str(key).isdigit()]
            if not ids:
                ctx.toast("Select sections first", level=ui.ToastLevel.WARNING)
                return
            try:
                db.delete_sections(ids)
                selected_state.value = []
                ctx.toast(f"Deleted {len(ids)} sections", level=ui.ToastLevel.SUCCESS)
            except DatabaseError:
                ctx.toast("Could not delete sections", level=ui.ToastLevel.ERROR)
            rows, total = db.list_sections(
                search=search_state.value,
                status=filters_state.value.get("status"),
                section_type=filters_state.value.get("section_type"),
                offset=0,
                limit=PAGE_SIZE,
            )
            rows_state.value = rows
            total_state.value = total
            page_state.value = 0

        def set_range(value: str) -> None:
            range_state.value = value

        _kpi_cards()
        chart = ui.Card(
            title="Visitors",
            description="Mobile and desktop traffic",
            children=ui.Column(
                ui.Row(
                    ui.Button(
                        "Last 7 days",
                        variant=(
                            ui.ButtonVariant.DEFAULT
                            if range_state.value == "7d"
                            else ui.ButtonVariant.OUTLINE
                        ),
                        on_click=lambda event: set_range("7d"),
                    ),
                    ui.Button(
                        "Last 30 days",
                        variant=(
                            ui.ButtonVariant.DEFAULT
                            if range_state.value == "30d"
                            else ui.ButtonVariant.OUTLINE
                        ),
                        on_click=lambda event: set_range("30d"),
                    ),
                    ui.Button(
                        "Last 3 months",
                        variant=(
                            ui.ButtonVariant.DEFAULT
                            if range_state.value == "3m"
                            else ui.ButtonVariant.OUTLINE
                        ),
                        on_click=lambda event: set_range("3m"),
                    ),
                    gap=8,
                ),
                ui.Chart(
                    data=_chart_data(range_state.value),
                    series=[
                        ui.ChartSeries(key="desktop", label="Desktop"),
                        ui.ChartSeries(key="mobile", label="Mobile"),
                    ],
                    kind=ui.ChartKind.AREA,
                    x_key="date",
                    height=300,
                ),
                gap=16,
            ),
        )

        section_kpis = db.kpis()
        outline_rows = db.list_sections(limit=100)[0]
        outline_table = ui.DataTable(
            [
                ui.TableColumn(key="name", header="Section", sortable=True),
                ui.TableColumn(key="section_type", header="Type", sortable=True),
                ui.TableColumn(key="status", header="Status", sortable=True),
                ui.TableColumn(key="reviewer", header="Reviewer", sortable=True),
            ],
            outline_rows,
            page_size=8,
            searchable=True,
            row_key="id",
            on_row_click=open_edit,
            empty_text="no sections in the outline",
        )

        type_summary = db.summary_by_type()
        performance_chart = ui.Chart(
            data=[
                {
                    "type": str(row["section_type"]),
                    "done": int(str(row["done"])),
                    "open": int(str(row["total"])) - int(str(row["done"])),
                }
                for row in type_summary
            ],
            series=[
                ui.ChartSeries(key="done", label="Done"),
                ui.ChartSeries(key="open", label="Open"),
            ],
            kind=ui.ChartKind.BAR,
            x_key="type",
            height=260,
        )

        reviewer_rows = db.summary_by_reviewer()
        reviewer_table = ui.Table(
            columns=[
                ui.TableColumn(key="reviewer", header="Reviewer"),
                ui.TableColumn(key="assigned", header="Assigned"),
                ui.TableColumn(key="done", header="Done"),
                ui.TableColumn(key="open", header="Open"),
            ],
            rows=[
                {
                    "reviewer": row["reviewer"],
                    "assigned": row["assigned"],
                    "done": row["done"],
                    "open": row["open"],
                }
                for row in reviewer_rows
            ],
        )

        focus_rows = db.list_sections(status="In Progress", limit=12)[0]
        focus_table = ui.DataTable(
            [
                ui.TableColumn(key="name", header="Section", sortable=True),
                ui.TableColumn(key="section_type", header="Type"),
                ui.TableColumn(key="target", header="Target"),
                ui.TableColumn(key="limit_value", header="Limit"),
                ui.TableColumn(key="reviewer", header="Reviewer"),
            ],
            focus_rows,
            page_size=6,
            searchable=True,
            row_key="id",
            on_row_click=open_edit,
            empty_text="no focus documents",
        )

        tabs = ui.Tabs(
            [
                ui.TabItem("outline", "Outline", content=outline_table),
                ui.TabItem(
                    "performance",
                    "Past Performance",
                    content=ui.Column(
                        ui.Grid(
                            ui.Card(
                                title="Total", description=str(section_kpis["total"])
                            ),
                            ui.Card(
                                title="Done", description=str(section_kpis["done"])
                            ),
                            ui.Card(
                                title="Open",
                                description=str(section_kpis["in_progress"]),
                            ),
                            ui.Card(
                                title="Completion",
                                description=f"{round((section_kpis['done'] / max(section_kpis['total'], 1)) * 100)}%",
                            ),
                            columns=ui.Responsive(base=2, xl=4),
                            gap=12,
                        ),
                        performance_chart,
                        gap=16,
                    ),
                ),
                ui.TabItem("personnel", "Key Personnel", content=reviewer_table),
                ui.TabItem(
                    "focus",
                    "Focus Documents",
                    content=ui.Column(
                        ui.Text(
                            "In-progress sections ordered for immediate attention.",
                            variant=ui.TextVariant.MUTED,
                        ),
                        focus_table,
                        gap=12,
                    ),
                ),
            ],
            value=tab_state.value,
            on_change=lambda event: setattr(tab_state, "value", event.value),
        )

        table = ui.DataTable(
            [
                ui.TableColumn(key="name", header="Section", sortable=True),
                ui.TableColumn(
                    key="section_type", header="Type", sortable=True, filterable=True
                ),
                ui.TableColumn(
                    key="status", header="Status", sortable=True, filterable=True
                ),
                ui.TableColumn(key="target", header="Target", sortable=True),
                ui.TableColumn(key="limit_value", header="Limit", sortable=True),
                ui.TableColumn(
                    key="reviewer", header="Reviewer", sortable=True, filterable=True
                ),
            ],
            rows_state.value,
            page_size=PAGE_SIZE,
            searchable=True,
            search_placeholder="search sections...",
            row_key="id",
            selected_keys=selected_state.value,
            on_selection_change=lambda keys: setattr(selected_state, "value", keys),
            server_side=True,
            total_rows=total_state.value,
            page_index=page_state.value,
            search=search_state.value,
            filters=filters_state.value,
            sorting=sorting_state.value,
            on_query_change=query_changed,
            on_row_click=open_edit,
        )

        create_dialog = ui.Dialog(
            ui.Form(
                ui.Field(
                    ui.Input(
                        name="name",
                        value=create_name,
                        on_change=lambda event: setattr(
                            create_name, "value", event.value
                        ),
                        required=True,
                    ),
                    label="Section name",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in SECTION_TYPES],
                        name="section_type",
                        value=create_type,
                        on_change=lambda event: setattr(
                            create_type, "value", event.value
                        ),
                    ),
                    label="Section type",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in STATUSES],
                        name="status",
                        value=create_status,
                        on_change=lambda event: setattr(
                            create_status, "value", event.value
                        ),
                    ),
                    label="Status",
                ),
                ui.Field(
                    ui.Input(
                        name="target",
                        type="number",
                        value=create_target,
                        on_change=lambda event: setattr(
                            create_target, "value", event.value
                        ),
                    ),
                    label="Target",
                ),
                ui.Field(
                    ui.Input(
                        name="limit",
                        type="number",
                        value=create_limit,
                        on_change=lambda event: setattr(
                            create_limit, "value", event.value
                        ),
                    ),
                    label="Limit",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in REVIEWERS],
                        name="reviewer",
                        value=create_reviewer,
                        on_change=lambda event: setattr(
                            create_reviewer, "value", event.value
                        ),
                    ),
                    label="Reviewer",
                ),
                on_submit=submit_create,
                class_name="space-y-3",
            ),
            trigger=ui.Button("Quick Create", icon="plus"),
            title="Create section",
            description="Add a new document section to the workspace.",
            open=quick_open.value,
            on_open_change=lambda event: setattr(quick_open, "value", event.open),
        )

        edit_dialog = ui.Dialog(
            ui.Form(
                ui.Field(
                    ui.Input(
                        name="name",
                        value=edit_name,
                        on_change=lambda event: setattr(
                            edit_name, "value", event.value
                        ),
                        required=True,
                    ),
                    label="Section name",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in SECTION_TYPES],
                        name="section_type",
                        value=edit_type,
                        on_change=lambda event: setattr(
                            edit_type, "value", event.value
                        ),
                    ),
                    label="Section type",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in STATUSES],
                        name="status",
                        value=edit_status,
                        on_change=lambda event: setattr(
                            edit_status, "value", event.value
                        ),
                    ),
                    label="Status",
                ),
                ui.Field(
                    ui.Input(
                        name="target",
                        type="number",
                        value=edit_target,
                        on_change=lambda event: setattr(
                            edit_target, "value", event.value
                        ),
                    ),
                    label="Target",
                ),
                ui.Field(
                    ui.Input(
                        name="limit",
                        type="number",
                        value=edit_limit,
                        on_change=lambda event: setattr(
                            edit_limit, "value", event.value
                        ),
                    ),
                    label="Limit",
                ),
                ui.Field(
                    ui.Select(
                        [ui.SelectOption(value, value) for value in REVIEWERS],
                        name="reviewer",
                        value=edit_reviewer,
                        on_change=lambda event: setattr(
                            edit_reviewer, "value", event.value
                        ),
                    ),
                    label="Reviewer",
                ),
                on_submit=submit_edit,
                class_name="space-y-3",
            ),
            title="Edit section",
            description="Update metadata, status, targets and reviewer assignment.",
            open=edit_open.value,
            on_open_change=lambda event: setattr(edit_open, "value", event.open),
        )

        content = ui.Column(
            ui.Row(
                ui.Column(
                    ui.Heading("Documents", level=1),
                    ui.Text(
                        "Manage sections, reviewers, targets and delivery status.",
                        variant=ui.TextVariant.MUTED,
                    ),
                    gap=4,
                ),
                create_dialog,
                justify=ui.Justify.BETWEEN,
                align=ui.Align.CENTER,
            ),
            _kpi_cards(),
            chart,
            tabs,
            ui.Card(
                title="Document sections",
                description=f"{total_state.value} sections",
                children=ui.Column(
                    ui.Row(
                        ui.Button(
                            "Delete selected",
                            variant=ui.ButtonVariant.DESTRUCTIVE,
                            on_click=delete_selected,
                        ),
                        ui.Text(
                            f"Selected: {len(selected_state.value)}",
                            variant=ui.TextVariant.MUTED,
                        ),
                        justify=ui.Justify.BETWEEN,
                        align=ui.Align.CENTER,
                    ),
                    table,
                    gap=12,
                ),
            ),
            edit_dialog,
            gap=20,
            width="100%",
            max_width=1440,
            padding=24,
            margin=(0, "auto"),
        )
        return content

    if path == "/analytics":
        range_state = ctx.state("30d", key="analytics-range")
        return ui.Column(
            ui.Heading("Analytics", level=1),
            ui.Text(
                "Workspace traffic and document activity.", variant=ui.TextVariant.MUTED
            ),
            _kpi_cards(),
            ui.Card(
                title="Visitors",
                children=ui.Chart(
                    data=_chart_data(range_state.value),
                    series=[
                        ui.ChartSeries(key="desktop", label="Desktop"),
                        ui.ChartSeries(key="mobile", label="Mobile"),
                    ],
                    kind=ui.ChartKind.AREA,
                    x_key="date",
                    height=320,
                ),
            ),
            gap=20,
            width="100%",
            max_width=1440,
            padding=24,
            margin=(0, "auto"),
        )

    if path == "/settings":
        ctx.state("light", key="settings-theme")
        return ui.Column(
            ui.Heading("Settings", level=1),
            ui.Card(
                title="Appearance",
                children=ui.ThemeToggle(),
            ),
            ui.Card(
                title="Workspace",
                children=ui.Text(
                    "Document workspace settings are stored with the application.",
                    variant=ui.TextVariant.MUTED,
                ),
            ),
            gap=20,
            width="100%",
            max_width=960,
            padding=24,
            margin=(0, "auto"),
        )

    title = path.strip("/").replace("-", " ").title() or "Home"
    return ui.Column(
        ui.Heading(title, level=1),
        ui.Text(
            "This workspace section is available from the sidebar.",
            variant=ui.TextVariant.MUTED,
        ),
        gap=12,
        width="100%",
        max_width=960,
        padding=24,
        margin=(0, "auto"),
    )


def _shell(path: str, ctx: ui.Context, content: ui.Component) -> ui.Component:
    return ui.Row(
        _sidebar(path),
        ui.Column(
            ui.Row(
                ui.ThemeToggle(),
                justify=ui.Justify.END,
                align=ui.Align.CENTER,
            ),
            content,
            gap=16,
            width="100%",
        ),
        gap=0,
        width="100%",
        min_height="100vh",
    )


app = ui.App("Document Workspace")
app.theme.configure(font_family="Geist", mono_font_family="Geist Mono")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    return _shell("/", ctx, _page_content("/", ctx))


@app.page("/dashboard")
def dashboard(ctx: ui.Context) -> ui.Component:
    return _shell("/dashboard", ctx, _page_content("/dashboard", ctx))


@app.page("/lifecycle")
def lifecycle(ctx: ui.Context) -> ui.Component:
    return _shell("/lifecycle", ctx, _page_content("/lifecycle", ctx))


@app.page("/analytics")
def analytics(ctx: ui.Context) -> ui.Component:
    return _shell("/analytics", ctx, _page_content("/analytics", ctx))


@app.page("/projects")
def projects(ctx: ui.Context) -> ui.Component:
    return _shell("/projects", ctx, _page_content("/projects", ctx))


@app.page("/team")
def team(ctx: ui.Context) -> ui.Component:
    return _shell("/team", ctx, _page_content("/team", ctx))


@app.page("/data-library")
def data_library(ctx: ui.Context) -> ui.Component:
    return _shell("/data-library", ctx, _page_content("/data-library", ctx))


@app.page("/reports")
def reports(ctx: ui.Context) -> ui.Component:
    return _shell("/reports", ctx, _page_content("/reports", ctx))


@app.page("/word-assistant")
def word_assistant(ctx: ui.Context) -> ui.Component:
    return _shell("/word-assistant", ctx, _page_content("/word-assistant", ctx))


@app.page("/more")
def more(ctx: ui.Context) -> ui.Component:
    return _shell("/more", ctx, _page_content("/more", ctx))


@app.page("/settings")
def settings(ctx: ui.Context) -> ui.Component:
    return _shell("/settings", ctx, _page_content("/settings", ctx))


@app.page("/help")
def help_page(ctx: ui.Context) -> ui.Component:
    return _shell("/help", ctx, _page_content("/help", ctx))


@app.page("/search")
def search(ctx: ui.Context) -> ui.Component:
    return _shell("/search", ctx, _page_content("/search", ctx))


if __name__ == "__main__":
    app.run()
