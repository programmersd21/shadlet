import shadlet as ui

app = ui.App("Component patterns")


@app.page("/")
def showcase(ctx: ui.Context) -> ui.Component:
    notifications = ctx.state(True, key="notifications")
    plan = ctx.state("starter", key="plan")

    def change_plan(event: ui.ChangeEvent) -> None:
        plan.value = event.value

    return ui.Column(
        ui.Row(
            ui.Column(
                ui.Heading("Component patterns", level=1),
                ui.Text(
                    "Compose accessible shadcn/ui-based components with Python.",
                    variant=ui.TextVariant.MUTED,
                ),
                gap=4,
            ),
            ui.ThemeToggle(),
            justify=ui.Justify.BETWEEN,
            align=ui.Align.CENTER,
        ),
        ui.Grid(
            ui.Card(
                title="Actions",
                description="Variants communicate the importance of an action.",
                children=ui.Column(
                    ui.Wrap(
                        ui.Button("Primary", on_click=lambda event: ctx.toast("Saved")),
                        ui.Button("Secondary", variant=ui.ButtonVariant.SECONDARY),
                        gap=8,
                    ),
                    ui.Wrap(
                        ui.Button("Outline", variant=ui.ButtonVariant.OUTLINE),
                        ui.Button("Ghost", variant=ui.ButtonVariant.GHOST),
                        ui.Button("Disabled", disabled=True),
                        gap=8,
                    ),
                    gap=12,
                ),
            ),
            ui.Card(
                title="Fields and state",
                description="Keep labels visible and bind committed values to Python state.",
                children=ui.Column(
                    ui.Field(
                        ui.Select(
                            [
                                ui.SelectOption("starter", "Starter"),
                                ui.SelectOption("team", "Team"),
                                ui.SelectOption("enterprise", "Enterprise"),
                            ],
                            value=plan.value,
                            name="plan",
                            on_change=change_plan,
                        ),
                        label="Plan",
                        description=f"Selected: {plan.value}",
                    ),
                    ui.Switch(
                        checked=notifications.value,
                        label="Email notifications",
                        description="Receive updates about your workspace.",
                        on_change=lambda event: setattr(
                            notifications, "value", event.value
                        ),
                    ),
                    gap=16,
                ),
            ),
            ui.Card(
                title="Tabs and disclosure",
                children=ui.Column(
                    ui.Tabs(
                        [
                            ui.TabItem(
                                "overview",
                                "Overview",
                                ui.Text("Tabs organize related views."),
                            ),
                            ui.TabItem(
                                "activity",
                                "Activity",
                                ui.Text("Each tab panel is composed in Python."),
                            ),
                        ]
                    ),
                    ui.Accordion(
                        [
                            ui.AccordionItem(
                                "keyboard",
                                "Keyboard support",
                                ui.Text(
                                    "Use the keyboard to move through tabs and disclosure controls."
                                ),
                            ),
                            ui.AccordionItem(
                                "composition",
                                "Composition",
                                ui.Text(
                                    "Use component slots for triggers, footers, and panel content."
                                ),
                            ),
                        ]
                    ),
                    gap=16,
                ),
            ),
            ui.Card(
                title="Feedback and overlays",
                children=ui.Column(
                    ui.Alert(
                        title="Heads up",
                        description="Use an alert for persistent page feedback.",
                    ),
                    ui.Dialog(
                        ui.Text("Dialog content is rendered in an accessible overlay."),
                        trigger=ui.Button(
                            "Open dialog", variant=ui.ButtonVariant.OUTLINE
                        ),
                        title="A composed dialog",
                        description="The trigger, content, and footer use named slots.",
                        footer=ui.Button("Done"),
                    ),
                    gap=12,
                ),
            ),
            columns=ui.Responsive(base=1, lg=2),
            gap=16,
        ),
        ui.Box(
            ui.Text("Explore the full supported set in the component catalogue."),
            as_="footer",
            class_name="border-t pt-6 text-muted-foreground",
        ),
        gap=24,
        width="100%",
        max_width=1100,
        margin=(0, "auto"),
        padding=24,
    )


if __name__ == "__main__":
    app.run()
