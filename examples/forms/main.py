import shadlet as ui
from pydantic import BaseModel, Field

app = ui.App("Validated form")


class ContactRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(
        min_length=5,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    topic: str
    message: str = Field(min_length=10, max_length=1000)


@app.page("/")
def contact(ctx: ui.Context) -> ui.Component:
    errors = ctx.state({}, key="contact-errors")
    form_error = ctx.state("", key="contact-form-error")

    def submit(values: ContactRequest) -> None:
        ctx.toast(
            "Message received",
            description=f"Thanks, {values.name}. This demo does not send email.",
        )

    return ui.Center(
        ui.Column(
            ui.Heading("Contact us", level=1),
            ui.Text(
                "A server-validated form with useful field-level feedback.",
                variant=ui.TextVariant.MUTED,
            ),
            ui.pydantic_form(
                ContactRequest,
                ui.Field(
                    ui.Input(name="name", auto_complete="name", required=True),
                    label="Name",
                    required=True,
                    error=errors.value.get("name"),
                    invalid="name" in errors.value,
                ),
                ui.Field(
                    ui.Input(
                        name="email",
                        type="email",
                        auto_complete="email",
                        required=True,
                    ),
                    label="Email",
                    required=True,
                    error=errors.value.get("email"),
                    invalid="email" in errors.value,
                ),
                ui.Field(
                    ui.Select(
                        [
                            ui.SelectOption("support", "Product support"),
                            ui.SelectOption("feedback", "Feedback"),
                            ui.SelectOption("other", "Other"),
                        ],
                        name="topic",
                        required=True,
                        aria_label="Topic",
                    ),
                    label="Topic",
                    required=True,
                    error=errors.value.get("topic"),
                    invalid="topic" in errors.value,
                ),
                ui.Field(
                    ui.Textarea(name="message", rows=5, required=True),
                    label="Message",
                    description="At least 10 characters.",
                    required=True,
                    error=errors.value.get("message"),
                    invalid="message" in errors.value,
                ),
                ui.Text(form_error.value, variant=ui.TextVariant.MUTED)
                if form_error.value
                else None,
                ui.Button("Send message", type="submit"),
                on_submit=submit,
                field_errors=errors,
                form_error=form_error,
                class_name="grid gap-5",
            ),
            max_width=560,
            gap=16,
            padding=24,
        ),
        min_height="100vh",
        padding=24,
    )


if __name__ == "__main__":
    app.run()
