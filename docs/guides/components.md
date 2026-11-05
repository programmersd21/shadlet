# components

shadlet's built-in components are available immediately after installation.
See the [component catalogue](../components/catalogue.md) for the supported set;
full upstream shadcn/ui parity is not claimed. No `shadlet add` command exists.

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

`ui.CodeBlock` presents plain code or terminal output with an optional title,
language label, line numbers, and copy button:

```python
ui.CodeBlock("print('hello')", title="example.py", language="python", line_numbers=True)
```

Copy uses the browser clipboard API and announces success or failure to assistive
technology. Syntax highlighting is not included; code is rendered as text.

`ui.Marker` renders semantically highlighted text with the HTML `<mark>` element:

```python
ui.Text("Search result: ", ui.Marker(""))
```

Use it to highlight text in context, such as a search match. It follows the
active theme and accepts `class_name` for local styling.
