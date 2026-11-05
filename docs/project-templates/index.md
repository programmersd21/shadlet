# project templates

scaffold a new project from a built-in starter:

```bash
shadlet create my-app
shadlet create my-dashboard --template dashboard
shadlet create my-site --template landing-page
shadlet create my-settings --template settings
shadlet create my-auth --template auth
shadlet create my-admin --template crud
```

available built-ins are `minimal`, `dashboard`, `landing-page`, `settings`, `auth`, and `crud`. each
includes a validated `shadlet-template.toml`, a Python project manifest, and
editable source. the `--target` option can select a different output directory:

The landing page template demonstrates responsive sections, in-page navigation,
feature and use case cards, an open-source adoption presentation, FAQ accordion,
theme control, and footer. Its sample pricing tiers are not commercial
plans.

the settings starter demonstrates profile, account, appearance, and notification
sections with session-local save feedback. connect save and preference events to
your own authenticated persistence layer before using it for real accounts.

The `auth` starter includes login, registration, and reset-request interfaces;
its login and reset behavior is a local UI demo, not an authentication provider.
The `crud` starter demonstrates search, sorting, pagination, status filters,
create, edit, and delete against a process-local sample repository.

```bash
shadlet create my-app --target ./projects/my-app
```

templates can declare text variables and metadata. override declared values
with repeatable `--var KEY=VALUE` options:

```bash
shadlet create my-app --var "title=customer portal"
```

the project name automatically replaces a declared `project_name` variable.
shadlet validates the manifest and minimum supported shadlet version before
reporting success; it does not install dependencies or execute template setup
scripts.

to use a github-hosted template or author your own manifest, see the
[github template guide](github.md).
