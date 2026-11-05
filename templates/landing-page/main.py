import shadlet as ui

app = ui.App("{{ title }}")


def section_heading(eyebrow: str, title: str, description: str):
    return ui.Column(
        ui.Text(
            eyebrow.upper(),
            class_name="text-xs font-semibold tracking-widest text-primary",
        ),
        ui.Heading(title, level=2),
        ui.Text(description, variant=ui.TextVariant.MUTED, class_name="max-w-2xl"),
        gap=8,
    )


@app.page("/")
def home(ctx: ui.Context):
    navigation = ui.Box(
        ui.Container(
            ui.Row(
                ui.Link(
                    ui.Row(
                        ui.Icon("blocks", size=20),
                        ui.Text(
                            "shadlet", as_="span", class_name="text-lg font-semibold"
                        ),
                        align=ui.Align.CENTER,
                        gap=8,
                    ),
                    href="#top",
                    class_name="no-underline",
                ),
                ui.Row(
                    ui.Link("Features", href="#features"),
                    ui.Link("Use cases", href="#use-cases"),
                    ui.Link("Pricing", href="#pricing"),
                    ui.Link("FAQ", href="#faq"),
                    ui.ThemeToggle(),
                    ui.Link(
                        "Get started",
                        href="#pricing",
                        class_name="rounded-md bg-primary px-4 py-2 text-primary-foreground no-underline",
                    ),
                    align=ui.Align.CENTER,
                    gap=20,
                    class_name="flex-wrap",
                ),
                align=ui.Align.CENTER,
                justify=ui.Justify.BETWEEN,
                gap=16,
                class_name="flex-wrap py-4",
            ),
            width="100%",
            max_width=1152,
            padding=(0, 24),
            margin=(0, "auto"),
        ),
        as_="nav",
        class_name="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
    )

    hero = ui.Container(
        ui.Box(
            ui.Column(
                ui.Badge(
                    "Python-first · React-rendered", variant=ui.BadgeVariant.SECONDARY
                ),
                ui.Heading(
                    "Build the product you imagined.",
                    level=1,
                    class_name="text-5xl font-bold tracking-tight sm:text-6xl",
                ),
                ui.Text(
                    "Compose polished, interactive web applications in Python. Keep your business logic in the backend and let React render a thoughtful interface.",
                    variant=ui.TextVariant.LEAD,
                    class_name="max-w-2xl",
                ),
                ui.Row(
                    ui.Link(
                        "Explore the framework",
                        href="https://github.com/programmersd21/shadlet",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                        class_name="rounded-md bg-primary px-5 py-3 text-primary-foreground no-underline",
                    ),
                    ui.Link("See what you can build", href="#features"),
                    gap=16,
                    align=ui.Align.CENTER,
                    wrap="wrap",
                ),
                ui.Text(
                    "Open source · Python API · React 19 renderer",
                    variant=ui.TextVariant.SMALL,
                ),
                gap=24,
                align=ui.Align.START,
                class_name="max-w-3xl",
            ),
            as_="section",
            id="top",
            class_name="flex min-h-[34rem] items-center py-24 sm:py-32",
        ),
        width="100%",
        max_width=1152,
        padding=(0, 24),
        margin=(0, "auto"),
    )

    features = ui.Container(
        ui.Column(
            section_heading(
                "A better foundation",
                "Python for the product. React for the pixels.",
                "Use the tools you already trust to build complete interfaces, from the first form to a data-rich admin workspace.",
            ),
            ui.Grid(
                ui.Card(
                    ui.Icon("workflow", size=24, class_name="text-primary"),
                    ui.Heading("One application language", level=3),
                    ui.Text(
                        "Compose pages and handle events in Python, close to your models and application services."
                    ),
                    class_name="h-full",
                ),
                ui.Card(
                    ui.Icon("component", size=24, class_name="text-primary"),
                    ui.Heading("Purposeful components", level=3),
                    ui.Text(
                        "Build with accessible controls, menus, dialogs, tables, charts, and layouts."
                    ),
                    class_name="h-full",
                ),
                ui.Card(
                    ui.Icon("refresh-cw", size=24, class_name="text-primary"),
                    ui.Heading("Reactive by design", level=3),
                    ui.Text(
                        "Update session-scoped state from Python handlers and keep the browser interface in sync."
                    ),
                    class_name="h-full",
                ),
                columns=ui.Responsive(base=1, md=3),
                gap=16,
                as_="section",
                id="features",
            ),
            gap=32,
            class_name="py-24 sm:py-28",
        ),
        width="100%",
        max_width=1152,
        padding=(0, 24),
        margin=(0, "auto"),
    )

    use_cases = ui.Container(
        ui.Column(
            section_heading(
                "Made for real work",
                "A familiar stack for the whole application.",
                "Keep integrations and domain rules in Python while composing product surfaces from reusable pieces.",
            ),
            ui.Grid(
                ui.Card(
                    ui.Heading("Internal tools", level=3),
                    ui.Text(
                        "Bring operational views, searchable tables, and workflow actions together."
                    ),
                ),
                ui.Card(
                    ui.Heading("Customer portals", level=3),
                    ui.Text(
                        "Compose account pages and forms while keeping application rules in your Python backend."
                    ),
                ),
                ui.Card(
                    ui.Heading("Analytics", level=3),
                    ui.Text(
                        "Pair metrics and charts with the data access and business logic you already maintain."
                    ),
                ),
                columns=ui.Responsive(base=1, md=3),
                gap=16,
                as_="section",
                id="use-cases",
            ),
            gap=32,
            class_name="border-y bg-muted/30 py-24 sm:py-28",
        ),
        width="100%",
        max_width=1152,
        padding=(0, 24),
        margin=(0, "auto"),
    )

    pricing = ui.Container(
        ui.Column(
            section_heading(
                "Start where you are",
                "Open source, with room to grow.",
                " is an open-source framework. These example tiers describe common ways teams adopt it; they are not paid plans.",
            ),
            ui.Grid(
                ui.Card(
                    ui.Heading("Explore", level=3),
                    ui.Text(
                        "For learning and prototypes.", variant=ui.TextVariant.MUTED
                    ),
                    ui.Heading("Free", level=2),
                    ui.Text("Use the framework, examples, and built-in components."),
                    footer=ui.Link(
                        "Read the quick start",
                        href="https://github.com/programmersd21/shadlet",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                    class_name="h-full",
                ),
                ui.Card(
                    ui.Badge(
                        "Popular starting point", variant=ui.BadgeVariant.SECONDARY
                    ),
                    ui.Heading("Build", level=3),
                    ui.Text("For an application team.", variant=ui.TextVariant.MUTED),
                    ui.Heading("Your stack", level=2),
                    ui.Text(
                        "Connect your own identity, database, deployment, and observability services."
                    ),
                    footer=ui.Link(
                        "Browse the guides",
                        href="https://github.com/programmersd21/shadlet/tree/main/docs",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                    class_name="h-full border-primary",
                ),
                ui.Card(
                    ui.Heading("Extend", level=3),
                    ui.Text(
                        "For specialized interfaces.", variant=ui.TextVariant.MUTED
                    ),
                    ui.Heading("Compose", level=2),
                    ui.Text(
                        "Author trusted extensions and integrate existing Python application code."
                    ),
                    footer=ui.Link(
                        "Learn about extensions",
                        href="https://github.com/programmersd21/shadlet/tree/main/docs/extensions.md",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                    class_name="h-full",
                ),
                columns=ui.Responsive(base=1, md=3),
                gap=16,
                as_="section",
                id="pricing",
            ),
            gap=32,
            class_name="py-24 sm:py-28",
        ),
        width="100%",
        max_width=1152,
        padding=(0, 24),
        margin=(0, "auto"),
    )

    faq = ui.Container(
        ui.Column(
            section_heading(
                "Common questions",
                "A few things to know before you start.",
                "Understand the framework boundaries and connect the services your application needs.",
            ),
            ui.Box(
                ui.Accordion(
                    [
                        ui.AccordionItem(
                            "language",
                            "Do I need to write React?",
                            "You build application pages and handlers with Python. React renders the browser UI; custom React extensions are available for specialized needs.",
                        ),
                        ui.AccordionItem(
                            "auth",
                            "Does  include authentication?",
                            "No built-in authentication provider is included. Integrate an identity provider and enforce authorization in your backend.",
                        ),
                        ui.AccordionItem(
                            "state",
                            "Where is session state stored?",
                            "The current runtime keeps sessions and task state in process memory. Plan shared state and session affinity before multi-worker deployment.",
                        ),
                        ui.AccordionItem(
                            "deploy",
                            "Can I connect my existing services?",
                            "Yes. Call your Python services and integrations from application handlers, and choose the database, storage, and deployment setup that fits your application.",
                        ),
                    ],
                    class_name="w-full max-w-3xl",
                ),
                as_="section",
                id="faq",
                class_name="w-full",
            ),
            gap=32,
            class_name="border-t py-24 sm:py-28",
        ),
        width="100%",
        max_width=1152,
        padding=(0, 24),
        margin=(0, "auto"),
    )

    footer = ui.Box(
        ui.Container(
            ui.Row(
                ui.Column(
                    ui.Text("shadlet", class_name="font-semibold"),
                    ui.Text(
                        "A Python-first framework for interactive web applications.",
                        variant=ui.TextVariant.MUTED,
                    ),
                    gap=8,
                ),
                ui.Row(
                    ui.Link(
                        "GitHub",
                        href="https://github.com/programmersd21/shadlet",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                    ui.Link(
                        "Documentation",
                        href="https://github.com/programmersd21/shadlet/tree/main/docs",
                        external=True,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                    ui.Link("Back to top", href="#top"),
                    gap=16,
                    wrap="wrap",
                ),
                align=ui.Align.CENTER,
                justify=ui.Justify.BETWEEN,
                gap=24,
                wrap="wrap",
            ),
            width="100%",
            max_width=1152,
            padding=24,
            margin=(0, "auto"),
        ),
        as_="footer",
        class_name="border-t",
    )

    return ui.Column(navigation, hero, features, use_cases, pricing, faq, footer, gap=0)


if __name__ == "__main__":
    app.run()
