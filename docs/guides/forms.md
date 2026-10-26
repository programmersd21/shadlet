# forms

use `ui.Form` with `on_submit`. the handler receives a `SubmitEvent` with `values` containing the form data.

```python
ui.Form(
    ui.Input(placeholder="name"),
    ui.Button("submit", type="submit"),
    on_submit=lambda e: print(e.values),
)
```
