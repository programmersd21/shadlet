# compatibility

the vendored upstream pin is recorded in
`tooling/compatibility/vendored-components.json`.

the generated [component compatibility matrix](../components/compatibility-matrix.md)
is the human-readable view. its machine-readable source is
`tooling/compatibility/component-matrix.json`, produced by
`tooling/compatibility/generate_matrix.py` from:

- the `shadlet.components` classes and their protocol `type` values,
- the renderer builtin adapter registry in
  `packages/renderer/src/runtime/registry.tsx`,
- `tooling/compatibility/component-coverage.json`.

run `python tooling/compatibility/generate_matrix.py` after changing component
support, and run it with `--check` to verify the checked-in reports. `partial`
means a python component and renderer adapter exist and are covered by smoke
tests, but the vendored shadcn/ui component exposes richer props, events,
keyboard behavior, or accessibility semantics than shadlet currently maps.
