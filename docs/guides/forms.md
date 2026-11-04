# forms

## basic forms

use `ui.Form` with `on_submit`. the handler receives a `SubmitEvent` whose
`values` mapping contains the named form controls.

```python
import shadlet as ui

ui.Form(
    ui.Field(ui.Input(name="name"), label="name"),
    ui.Button("submit", type="submit"),
    on_submit=lambda event: print(event.values),
)
```

Give every interactive control an accessible name using `ui.Field` with a
visible label, or `aria_label` on controls such as `Input`, `Select`,
`NativeSelect`, `RadioGroup`, `Combobox`, `Slider`, and `InputOTP`. Placeholder
text is not a substitute for a label.

## pydantic validation

`ui.pydantic_form` validates submitted values with a pydantic v2 model on the
server. browser values remain untrusted; validation always runs in python.

```python
from pydantic import BaseModel, Field
import shadlet as ui


class Signup(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    age: int = Field(ge=13)


app = ui.App("signup")


@app.page("/")
def signup(ctx: ui.Context):
    errors = ctx.state({}, key="signup-errors")
    form_error = ctx.state("", key="signup-error")

    def submit(values: Signup):
        ctx.toast(f"welcome, {values.username}")

    return ui.pydantic_form(
        Signup,
        ui.Field(
            ui.Input(name="username", required=True),
            label="username",
            error=errors.value.get("username"),
            invalid="username" in errors.value,
            required=True,
        ),
        ui.Field(
            ui.Input(name="age", type="number", required=True),
            label="age",
            error=errors.value.get("age"),
            invalid="age" in errors.value,
            required=True,
        ),
        ui.Text(form_error.value) if form_error.value else None,
        ui.Button("sign up", type="submit"),
        on_submit=submit,
        field_errors=errors,
        form_error=form_error,
    )
```

field errors are stored using dot-separated paths, including nested model
locations. a form-level message is stored in `form_error`. successful
validation clears both states and calls the handler with the validated model.
async handlers are supported by the normal event runtime.

the helper validates the model and reports errors, but it does not generate
controls from model metadata, infer labels, or track dirty/touched state.
applications choose their own control composition and reset behavior.
