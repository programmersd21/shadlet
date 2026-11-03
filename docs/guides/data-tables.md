# server-driven data tables

`ui.DataTable` supports a server-side mode for datasets too large to send to the
browser. in this mode the browser emits a validated `ui.DataTableQuery`, and
the application supplies only the requested page.

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

    def query_changed(query: ui.DataTableQuery):
        matching = records
        if query.search:
            term = query.search.casefold()
            matching = [row for row in records if term in row["name"].casefold()]
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
        start = query.page_index * query.page_size
        rows.value = matching[start : start + query.page_size]

    return ui.DataTable(
        [
            {"key": "id", "header": "id", "sortable": True},
            {"key": "name", "header": "name", "sortable": True},
            {"key": "group", "header": "group"},
        ],
        rows.value,
        server_side=True,
        total_rows=total.value,
        page_size=25,
        page_index=page_index.value,
        search=search.value,
        on_query_change=query_changed,
    )
```

`DataTableQuery` rejects unknown fields, out-of-range values, oversized
searches, duplicate sort keys, and sort/filter keys not declared by the table.
callbacks may be async. the application must perform filtering and sorting
using safe, declared fields; never splice client input into a database query.

server mode currently provides validated pagination, single or multi-key sort
payloads, search and filter payload validation. the built-in adapter does not
provide query cancellation, loading/error indicators, cross-page selection, or
column visibility. the example uses an in-memory dataset; production
applications should execute bounded database queries.
