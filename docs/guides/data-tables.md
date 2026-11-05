# server-driven data tables

`ui.DataTable` supports a server-side mode for datasets too large to send to the
browser. in this mode the browser emits a validated `ui.DataTableQuery`, and
the application supplies only the requested page.

set `row_key` to a non-empty, unique string or integer field when rows can move
between positions. duplicate or missing keys are rejected for the supplied
page; the renderer then uses the key as stable row identity.

```python
import shadlet as ui

records = [
    {"id": index, "name": f"user {index:05}", "group": f"group {index % 8}"}
    for index in range(10_000)
]

app = ui.App("users")


@app.page("/")
def users(ctx: ui.Context):
    rows = ctx.state(records[:25], key="users-page")
    total = ctx.state(len(records), key="users-total")
    page_index = ctx.state(0, key="users-index")
    search = ctx.state("", key="users-search")
    table_filters = ctx.state({}, key="users-filters")

    def query_changed(query: ui.DataTableQuery):
        matching = records
        if query.search:
            term = query.search.casefold()
            matching = [row for row in records if term in row["name"].casefold()]
        for key, value in query.filters.items():
            term = value.casefold()
            matching = [row for row in matching if term in str(row[key]).casefold()]
        if query.sorting:
            sort = query.sorting[0]
            matching = sorted(
                matching,
                key=lambda row: row[sort.key],
                reverse=sort.direction == "desc",
            )
        total.value = len(matching)
        page_index.value = query.page_index
        search.value = query.search
        table_filters.value = dict(query.filters)
        start = query.page_index * query.page_size
        rows.value = matching[start : start + query.page_size]

    return ui.DataTable(
        [
            {"key": "id", "header": "id", "sortable": True},
            {"key": "name", "header": "name", "sortable": True},
            {"key": "group", "header": "group", "filterable": True},
        ],
        rows.value,
        server_side=True,
        total_rows=total.value,
        page_size=25,
        page_index=page_index.value,
        search=search.value,
        filters=table_filters.value,
        on_query_change=query_changed,
    )
```

`DataTableQuery` rejects unknown fields, page sizes outside 1–500, out-of-range values, oversized
searches, duplicate sort keys, and sort/filter keys not declared by the table.
callbacks may be async. the application must perform filtering and sorting
using safe, declared fields; never splice client input into a database query.

mark a column `filterable=True` to render an accessible per-column text filter.
search, sorting, filters, and pagination all emit the same validated query
event; server-side search resets the requested page to zero. local mode applies
the same search and filter controls in the browser.
the `columns` menu lets users hide or show columns locally; visibility resets
when the component is remounted.

## selection and asynchronous queries

Selection is opt-in and requires a stable `row_key`. `selected_keys` is a
controlled set of keys, and `on_selection_change` receives normalized strings.
The select-all checkbox applies to the currently visible page; selections from
other pages are retained when the application keeps the full key list in state.

```python
selected = ctx.state([], key="selected-user-ids")
return ui.DataTable(
    columns,
    rows.value,
    row_key="id",
    selected_keys=selected.value,
    on_selection_change=lambda keys: setattr(selected, "value", keys),
)
```

In server-side mode, when a new query arrives the session cancels the previous
in-flight async `on_query_change` callback before starting the latest one.
Callbacks should use `asyncio` cancellation points and must not suppress
`asyncio.CancelledError`. Cancellation cannot undo database writes or work
already delegated to an external system; keep query callbacks read-only and
make external work independently cancellable where appropriate.

server-side requests can display reactive status and retry controls:

```python
return ui.DataTable(
    columns,
    rows.value,
    server_side=True,
    total_rows=total.value,
    loading=loading.value,
    error=error.value or None,
    on_retry=retry_query,
    on_query_change=query_changed,
)
```

while loading or showing an error, stale rows are hidden and table controls are
disabled.
set `loading` and `error` from application state, update them in the query
callback, and bind `on_retry` to an application-owned retry action. sortable
headers expose their current sort direction to assistive technology, and the
table scrolls horizontally on narrow screens.

The example uses an in-memory dataset; production applications should execute
bounded database queries and avoid using untrusted query values in SQL strings.
