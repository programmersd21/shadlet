# project templates

scaffold a new project from a built-in starter:

```bash
shadlet create my-app
shadlet create my-dashboard --template dashboard
shadlet create my-site --template landing-page
```

available built-ins are `minimal`, `dashboard`, and `landing-page`. each
includes a validated `shadlet-template.toml`, a Python project manifest, and
editable source. the `--target` option can select a different output directory:

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
