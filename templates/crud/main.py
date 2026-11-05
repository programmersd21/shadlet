import shadlet as ui
from shadlet import DataTableQuery

app = ui.App("{{ title }}")

INITIAL_PROJECTS = [
    {"id": "prj_001", "name": "Website refresh", "status": "In progress"},
    {"id": "prj_002", "name": "Mobile app", "status": "Planned"},
    {"id": "prj_003", "name": "Billing portal", "status": "Complete"},
    {"id": "prj_004", "name": "Design system", "status": "In progress"},
    {"id": "prj_005", "name": "Documentation", "status": "Planned"},
    {"id": "prj_006", "name": "API migration", "status": "Complete"},
]


def filter_projects(projects, query: DataTableQuery):
    result = list(projects)
    if query.search:
        search = query.search.casefold()
        result = [
            row
            for row in result
            if search in row["name"].casefold()
            or search in row["status"].casefold()
            or search in row["id"].casefold()
        ]
    for key, value in query.filters.items():
        result = [row for row in result if row.get(key) == value]
    for sort in reversed(query.sorting):
        result.sort(
            key=lambda row: str(row.get(sort.key, "")).casefold(),
            reverse=sort.direction == "desc",
        )
    start = query.page_index * query.page_size
    return result[start : start + query.page_size], len(result)


@app.page("/")
def projects(ctx: ui.Context):
    rows = ctx.state(INITIAL_PROJECTS, key="projects")
    name = ctx.state("", key="project_name")
    status = ctx.state("Planned", key="project_status")
    notice = ctx.state("", key="notice")
    error = ctx.state("", key="error")
    filter_status = ctx.state("all", key="filter_status")
    search = ctx.state("", key="search")
    page_index = ctx.state(0, key="page_index")
    sorting = ctx.state([], key="sorting")
    dialog_open = ctx.state(False, key="dialog_open")
    editing_id = ctx.state("", key="editing_id")
    delete_id = ctx.state("", key="delete_id")
    delete_open = ctx.state(False, key="delete_open")
    selected_id = ctx.state("", key="selected_id")

    def query_rows(query: DataTableQuery):
        search.value = query.search
        page_index.value = query.page_index
        sorting.value = [
            {"key": item.key, "direction": item.direction} for item in query.sorting
        ]
        effective_query = query.model_copy(
            update={
                "filters": {
                    **query.filters,
                    **(
                        {"status": filter_status.value}
                        if filter_status.value != "all"
                        else {}
                    ),
                }
            }
        )
        table_rows, count = filter_projects(rows.value, effective_query)
        if selected_id.value and not any(
            row["id"] == selected_id.value for row in table_rows
        ):
            selected_id.value = ""
        notice.value = f"Loaded {count} matching projects."

    def save_project(_event):
        normalized_name = name.value.strip()
        if not normalized_name:
            error.value = "Enter a project name."
            return
        if editing_id.value:
            rows.value = [
                {
                    **row,
                    "name": normalized_name,
                    "status": status.value,
                }
                if row["id"] == editing_id.value
                else row
                for row in rows.value
            ]
            notice.value = "Project updated."
        else:
            next_id = (
                max((int(row["id"].split("_")[1]) for row in rows.value), default=0) + 1
            )
            rows.value = [
                *rows.value,
                {
                    "id": f"prj_{next_id:03d}",
                    "name": normalized_name,
                    "status": status.value,
                },
            ]
            notice.value = "Project created."
        error.value = ""
        name.value = ""
        editing_id.value = ""
        dialog_open.value = False
        page_index.value = 0
        selected_id.value = ""

    def edit_project(event):
        selected = next((row for row in rows.value if row["id"] == event.value), None)
        if selected is None:
            return
        editing_id.value = selected["id"]
        name.value = selected["name"]
        status.value = selected["status"]
        dialog_open.value = True

    def request_delete(event):
        delete_id.value = event.value
        delete_open.value = True

    def select_visible_project(event):
        selected_id.value = str(event.value["id"])

    def confirm_delete(_event):
        rows.value = [row for row in rows.value if row["id"] != delete_id.value]
        delete_open.value = False
        delete_id.value = ""
        selected_id.value = ""
        page_index.value = 0
        notice.value = "Project deleted."

    def set_filter(event):
        filter_status.value = event.value
        page_index.value = 0
        selected_id.value = ""

    def open_create(_event):
        editing_id.value = ""
        name.value = ""
        status.value = "Planned"
        error.value = ""
        dialog_open.value = True

    query_filters = (
        {} if filter_status.value == "all" else {"status": filter_status.value}
    )
    query = DataTableQuery(
        page_index=page_index.value,
        page_size=5,
        sorting=sorting.value,
        search=search.value,
        filters=query_filters,
    )
    visible_rows, total_rows = filter_projects(rows.value, query)
    columns = [
        ui.TableColumn(key="name", header="Project", sortable=True),
        ui.TableColumn(key="status", header="Status", sortable=True),
        ui.TableColumn(key="id", header="ID", sortable=True),
    ]
    selected_row = next(
        (row for row in rows.value if row["id"] == selected_id.value), None
    )

    editor = ui.Dialog(
        ui.Column(
            ui.Field(
                "Project name",
                ui.Input(
                    value=name.value,
                    required=True,
                    on_change=lambda event: setattr(name, "value", event.value),
                ),
                error=error.value or None,
                invalid=bool(error.value),
            ),
            ui.Field(
                "Status",
                ui.Select(
                    ["Planned", "In progress", "Complete"],
                    value=status.value,
                    aria_label="Project status",
                    on_change=lambda event: setattr(status, "value", event.value),
                ),
            ),
            gap=16,
        ),
        title="Edit project" if editing_id.value else "Create project",
        description="Changes are kept in this process-local demo session.",
        footer=ui.Button("Save project", on_click=save_project),
        open=dialog_open.value,
        on_open_change=lambda event: setattr(dialog_open, "value", event.open),
    )
    confirmation = ui.AlertDialog(
        title="Delete project?",
        description="This removes the project from the demo list.",
        action=ui.Button(
            "Delete project", variant="destructive", on_click=confirm_delete
        ),
        cancel=ui.Button(
            "Cancel",
            variant="outline",
            on_click=lambda _event: setattr(delete_open, "value", False),
        ),
        open=delete_open.value,
        on_open_change=lambda event: setattr(delete_open, "value", event.open),
    )

    return ui.Column(
        ui.Row(
            ui.Column(
                ui.Heading("Projects", level=1),
                ui.Text("Manage a small session-local project catalogue."),
                gap=4,
            ),
            ui.Button("Create project", on_click=open_create),
            justify=ui.Justify.BETWEEN,
            align=ui.Align.CENTER,
        ),
        ui.Alert(notice.value, title="Done") if notice.value else None,
        ui.Row(
            ui.Text("Filter status"),
            ui.Select(
                [
                    {"value": "all", "label": "All statuses"},
                    "Planned",
                    "In progress",
                    "Complete",
                ],
                value=filter_status.value,
                aria_label="Filter by status",
                on_change=set_filter,
            ),
            gap=12,
            align=ui.Align.CENTER,
        ),
        ui.DataTable(
            columns,
            visible_rows,
            page_size=5,
            row_key="id",
            server_side=True,
            total_rows=total_rows,
            page_index=page_index.value,
            sorting=[
                {"key": item["key"], "direction": item["direction"]}
                for item in sorting.value
            ],
            search=search.value,
            filters=query_filters,
            on_query_change=query_rows,
            on_row_click=select_visible_project,
        ),
        ui.Row(
            ui.Text(
                f"Selected: {selected_row['name']}"
                if selected_row
                else "Select a project to edit or delete it."
            ),
            ui.Button(
                "Edit selected",
                variant="outline",
                disabled=selected_row is None,
                value=selected_id.value or None,
                on_click=edit_project,
            ),
            ui.Button(
                "Delete selected",
                variant="destructive",
                disabled=selected_row is None,
                value=selected_id.value or None,
                on_click=request_delete,
            ),
            align=ui.Align.CENTER,
            gap=12,
        ),
        editor,
        confirmation,
        gap=20,
        padding=32,
        width="100%",
        max_width=1100,
        margin=(0, "auto"),
    )


if __name__ == "__main__":
    app.run()
