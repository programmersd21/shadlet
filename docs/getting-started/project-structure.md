# project structure

a minimal shadlet project contains:

```text
my-app/
├── main.py
├── pyproject.toml
└── README.md
```

- `main.py` defines the application, pages and callbacks.
- `pyproject.toml` declares python dependencies.
- the renderer is provided by the installed shadlet package.

## repository layout

```text
shadlet/
├── packages/python/shadlet   python runtime
├── packages/renderer         react renderer
├── templates                 project templates
├── examples                  example applications
├── tests                     python tests
└── docs                      documentation
```
