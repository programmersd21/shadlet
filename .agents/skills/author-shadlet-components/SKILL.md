---
name: author-shadlet-components
description: Add or change a built-in Shadlet Python component and its React renderer implementation. Use for component API, protocol serialization, schemas, accessibility, tests, and catalogue documentation.
---

# Author Shadlet components

Treat a built-in component as a Python-to-browser contract, not just a React view.

## Workflow

1. Inspect a nearby component in `packages/python/shadlet/components/`, its renderer counterpart under `packages/renderer/src/`, the component catalogue, and shared protocol schema/fixtures before editing.
2. Keep the Python public API typed and serializable. Match snake_case Python options to renderer prop mapping; preserve omitted-versus-`None` semantics when relevant. Add runtime validation for public inputs.
3. Use the existing Base UI primitive where it provides the required interaction and focus behavior. Do not replace menus, popovers, dialogs, or comboboxes with nonfunctional generic HTML.
4. Implement controlled state and event dispatch through the existing protocol. Never serialize Python callbacks or add a second source of truth for server-owned state.
5. Cover meaningful variants, disabled/loading/error/empty states, keyboard behavior, focus management, semantic names, and dark theme where applicable.
6. Add Python serialization/API tests, renderer interaction/accessibility tests, and Playwright coverage for browser-only behavior when warranted. Update `docs/components/catalogue.md` and relevant component docs.
7. Run the targeted Python and renderer checks; report any check that could not be run.

## References

- `packages/python/shadlet/components/`
- `packages/renderer/src/`
- `packages/renderer/e2e/`
- `docs/architecture/protocol.md`
- `docs/guides/components.md`
- `docs/development/testing.md`
