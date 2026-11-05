---
name: build-shadlet-apps
description: Build or extend Python-first applications with Shadlet 0.6.0. Use for app structure, pages, reactive state, events, routes, forms, tables, charts, uploads, storage, themes, or deployment using APIs that exist in this repository.
---

# Build a Shadlet application

Use the quick start and runnable examples before inventing a new application pattern.

## Workflow

1. Confirm the installed Shadlet version and read `docs/getting-started/first-app.md` plus the guides for the feature involved.
2. Start with `import shadlet as ui`, `ui.App`, an `@app.page(...)` function, and `app.run()`; keep application rules and durable state in Python.
3. Compose built-in controls and layouts from `docs/components/catalogue.md`. Use `ctx.state(value, key=...)` for session-owned reactive state; assign a new container value instead of mutating it in place.
4. Bind real `on_*` handlers. Validate untrusted submissions in Python; use `ui.pydantic_form` for Pydantic v2 model validation and compose the fields explicitly.
5. For datasets use `ui.DataTable` with declared columns, validated `DataTableQuery`, stable `row_key`, and bounded backend queries. Keep database query construction parameterized.
6. Read `docs/limitations.md` before promising capabilities. The catalogue is not full shadcn/ui parity; auth and CRUD templates are local demos, not identity or durable database systems.
7. Add a focused test and document any new public behavior. Run the relevant Python, renderer, or browser checks described in `docs/development/testing.md`.

## References

- `docs/getting-started/first-app.md`
- `docs/guides/applications.md`
- `docs/guides/state.md`
- `docs/guides/events.md`
- `docs/guides/routing.md`
- `docs/guides/forms.md`
- `docs/guides/data-tables.md`
- `examples/README.md`
