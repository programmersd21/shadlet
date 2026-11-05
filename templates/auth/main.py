import shadlet as ui

app = ui.App("{{ title }}")


@app.page("/")
def login(ctx: ui.Context):
    email = ctx.state("", key="email")
    password = ctx.state("", key="password")
    error = ctx.state("", key="error")
    authenticated = ctx.state(False, key="authenticated")

    def submit(_event):
        if email.value.strip() and len(password.value) >= 8:
            authenticated.value = True
            error.value = ""
        else:
            authenticated.value = False
            error.value = "Enter an email and a password with at least 8 characters."

    if authenticated.value:
        content = ui.Alert(
            ui.Text(f"Signed in as {email.value}. This is demo-only session state."),
            variant=ui.AlertVariant.DEFAULT,
            title="Welcome",
        )
    else:
        content = ui.Column(
            ui.Heading("Sign in", level=1),
            ui.Text("Use any email and an 8-character password for this local demo."),
            ui.Field(
                "Email",
                ui.Input(
                    value=email.value,
                    type="email",
                    name="email",
                    required=True,
                    auto_complete="email",
                    on_change=lambda event: setattr(email, "value", event.value),
                ),
            ),
            ui.Field(
                "Password",
                ui.Input(
                    value=password.value,
                    type="password",
                    name="password",
                    required=True,
                    auto_complete="current-password",
                    on_change=lambda event: setattr(password, "value", event.value),
                ),
                description="At least 8 characters.",
            ),
            ui.Alert(error, variant=ui.AlertVariant.DESTRUCTIVE, title="Sign in failed")
            if error.value
            else None,
            ui.Button("Sign in", on_click=submit),
            ui.Link("Forgot password?", href="/reset"),
            ui.Link("Create an account", href="/register"),
            gap=16,
            class_name="w-full max-w-sm",
        )
    return ui.Container(content, min_height="100vh", padding=32)


@app.page("/register")
def register(ctx: ui.Context):
    name = ctx.state("", key="register_name")
    email = ctx.state("", key="register_email")
    password = ctx.state("", key="register_password")
    message = ctx.state("", key="register_message")

    def submit(_event):
        if not name.value.strip():
            message.value = "Enter your name."
        elif "@" not in email.value or "." not in email.value.rsplit("@", 1)[-1]:
            message.value = "Enter a valid email address."
        elif len(password.value) < 8:
            message.value = "Choose a password with at least 8 characters."
        else:
            message.value = "Demo registration complete. No account was created."

    return ui.Column(
        ui.Heading("Create an account", level=1),
        ui.Text("Registration UI demo. Connect this form to your identity provider."),
        ui.Field(
            "Name",
            ui.Input(
                value=name.value,
                name="name",
                auto_complete="name",
                on_change=lambda event: setattr(name, "value", event.value),
            ),
        ),
        ui.Field(
            "Email",
            ui.Input(
                value=email.value,
                type="email",
                name="email",
                auto_complete="email",
                on_change=lambda event: setattr(email, "value", event.value),
            ),
        ),
        ui.Field(
            "Password",
            ui.Input(
                value=password.value,
                type="password",
                name="password",
                auto_complete="new-password",
                on_change=lambda event: setattr(password, "value", event.value),
            ),
        ),
        ui.Alert(message.value, title="Registration") if message.value else None,
        ui.Button("Create account", on_click=submit),
        ui.Link("Back to sign in", href="/"),
        gap=16,
        padding=32,
        width="100%",
        max_width=480,
        margin=(0, "auto"),
    )


@app.page("/reset")
def reset_password(ctx: ui.Context):
    sent = ctx.state(False, key="reset_sent")
    email = ctx.state("", key="reset_email")
    error = ctx.state("", key="reset_error")

    def submit(_event):
        if "@" not in email.value or "." not in email.value.rsplit("@", 1)[-1]:
            error.value = "Enter a valid email address."
            sent.value = False
        else:
            error.value = ""
            sent.value = True

    return ui.Column(
        ui.Heading("Reset password", level=1),
        ui.Text("This demo shows the request flow; it does not send email."),
        ui.Field(
            "Email",
            ui.Input(
                value=email.value,
                type="email",
                name="email",
                required=True,
                auto_complete="email",
                on_change=lambda event: setattr(email, "value", event.value),
            ),
            error=error.value or None,
            invalid=bool(error.value),
        ),
        ui.Button("Send reset link", on_click=submit),
        ui.Text("If this were connected, reset instructions would be sent.")
        if sent.value
        else None,
        ui.Link("Back to sign in", href="/"),
        gap=16,
        padding=32,
        width="100%",
        max_width=480,
        margin=(0, "auto"),
    )


if __name__ == "__main__":
    app.run()
