---
name: author-shadlet-extensions
description: Create or maintain a Shadlet React component extension distributed as a Python package. Use for extension manifests, browser registration, assets, packaging, CLI workflows, and trust boundaries.
---

# Author Shadlet extensions

Extensions are trusted Python and browser code packaged with their assets; they are not sandboxed plugins.

## Workflow

1. Read `docs/extensions.md` and check whether the built-in catalogue already covers the use case.
2. Use `shadlet extension create`, then implement a namespaced Python component and matching React registration. Keep props JSON-compatible and send application actions through the provided dispatch bridge.
3. Declare assets with `ExtensionManifest`; resolve packaged files with `importlib.resources.files`, not the current working directory. Include entrypoint, stylesheet, and every referenced asset in the wheel.
4. Keep Python component props/events aligned with the browser adapter and test both. Do not load extension JavaScript from an unpinned CDN or package secrets in public assets.
5. Run `shadlet extension check`, build the extension, inspect the wheel, install it in a clean environment, and run the relevant browser test. Application runtime should use bundled extension assets and not require Node.js.
6. Document the extension trust boundary and supported Shadlet version range.

## References

- `docs/extensions.md`
- `tests/unit/test_extensions.py`
- `tests/integration/test_node_free_extension.py`
- `packages/renderer/e2e/runtime.spec.ts`
