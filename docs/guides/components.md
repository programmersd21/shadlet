# components

shadlet ships 56 built-in components based on shadcn/ui `base-vega`. they are available immediately after installation. no `shadlet add` command exists.

## usage

```python
import shadlet as ui

ui.Button("save", variant=ui.ButtonVariant.OUTLINE, size=ui.ButtonSize.SM)
```

string values are also accepted where appropriate:

```python
ui.Button("save", variant="outline")
```

## composition

children are passed positionally. named slots use keyword arguments such as `trigger`, `footer`, `header`.

```python
ui.Dialog(
    ui.Text("body"),
    trigger=ui.Button("open"),
    title="title",
)
```

## property mapping

python uses snake_case. the renderer maps to camelCase react props. omitted properties and explicit `None` are distinguished where it matters.

see the [component catalogue](../components/catalogue.md).
