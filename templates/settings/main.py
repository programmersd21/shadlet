import shadlet as ui

app = ui.App("{{ title }}")


def page_shell(content: ui.Component):
    return ui.Column(
        ui.Row(
            ui.Column(
                ui.Heading("Settings", level=1),
                ui.Text("Manage your profile and preferences."),
                gap=4,
            ),
            ui.ThemeToggle(),
            justify=ui.Justify.BETWEEN,
            align=ui.Align.CENTER,
        ),
        content,
        gap=24,
        padding=32,
        width="100%",
        max_width=960,
        margin=(0, "auto"),
    )


@app.page("/")
def settings(ctx: ui.Context):
    saved = ctx.state(False, key="saved")
    name = ctx.state("Alex Morgan", key="profile_name")
    email = ctx.state("alex@example.com", key="profile_email")
    language = ctx.state("English", key="language")
    timezone = ctx.state("UTC", key="timezone")
    product_updates = ctx.state(True, key="product_updates")
    security_alerts = ctx.state(True, key="security_alerts")
    weekly_summary = ctx.state(False, key="weekly_summary")

    def update(state, event):
        state.value = event.value
        saved.value = False

    def save(_event):
        saved.value = True

    profile = ui.Column(
        ui.Field(
            "Name",
            ui.Input(
                value=name.value,
                name="name",
                on_change=lambda event: update(name, event),
            ),
            description="Your public display name.",
        ),
        ui.Field(
            "Email",
            ui.Input(
                value=email.value,
                type="email",
                name="email",
                on_change=lambda event: update(email, event),
            ),
        ),
        ui.Button("Save profile", on_click=save),
        ui.Text("Changes saved.", class_name="text-sm text-muted-foreground")
        if saved.value
        else None,
        gap=16,
        class_name="max-w-xl",
    )
    account = ui.Column(
        ui.Field(
            "Language",
            ui.Select(
                ["English", "French", "German"],
                value=language.value,
                aria_label="Language",
                on_change=lambda event: update(language, event),
            ),
        ),
        ui.Field(
            "Timezone",
            ui.Select(
                ["UTC", "America/New_York", "Europe/London"],
                value=timezone.value,
                aria_label="Timezone",
                on_change=lambda event: update(timezone, event),
            ),
        ),
        ui.Text("Authentication and billing are managed by your application backend."),
        gap=16,
        class_name="max-w-xl",
    )
    appearance = ui.Column(
        ui.Text("Choose a theme for this browser session."),
        ui.ThemeToggle(),
        gap=16,
        class_name="max-w-xl",
    )
    notifications = ui.Column(
        ui.Field(
            "Product updates",
            ui.Switch(
                checked=product_updates.value,
                label="Product updates",
                on_change=lambda event: update(product_updates, event),
            ),
        ),
        ui.Field(
            "Security alerts",
            ui.Switch(
                checked=security_alerts.value,
                label="Security alerts",
                on_change=lambda event: update(security_alerts, event),
            ),
        ),
        ui.Field(
            "Weekly summary",
            ui.Switch(
                checked=weekly_summary.value,
                label="Weekly summary",
                on_change=lambda event: update(weekly_summary, event),
            ),
        ),
        gap=16,
        class_name="max-w-xl",
    )
    return page_shell(
        ui.Tabs(
            [
                ui.TabItem("Profile", "profile", profile),
                ui.TabItem("Account", "account", account),
                ui.TabItem("Appearance", "appearance", appearance),
                ui.TabItem("Notifications", "notifications", notifications),
            ],
            orientation=ui.Orientation.VERTICAL,
            class_name="w-full",
        )
    )


if __name__ == "__main__":
    app.run()
