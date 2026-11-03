# query parameter state

`Context.query_state` binds a reactive state slot to one query parameter. the
initial value is parsed from the current browser url; assigning a new value
updates the url without navigating away from the current page. updates replace
the current history entry by default; `history="push"` creates an entry that
can be revisited with browser back/forward. history navigation re-parses the
query value and re-renders the page.

```python
import shadlet as ui

app = ui.App("search")


@app.page("/search")
def search(ctx: ui.Context):
    page = ctx.query_state("page", 1)

    def next_page(event: ui.ClickEvent):
        page.value += 1

    return ui.Column(
        ui.Text(f"page: {page.value}"),
        ui.Button("next page", on_click=next_page),
    )
```

with no custom parser, `str`, `int`, `float`, and `bool` defaults determine the
query conversion. boolean values accept `true`, `false`, `1`, and `0`.
custom types can provide a parser and serializer:

```python
from datetime import date

selected = ctx.query_state(
    "date",
    date.today(),
    parse=date.fromisoformat,
    serialize=date.isoformat,
)
```

state is isolated to the active session and route. query values are URL input,
so parsing errors are reported as invalid navigation rather than silently
falling back to the default. values must still be serializable by the shadlet
state protocol.
