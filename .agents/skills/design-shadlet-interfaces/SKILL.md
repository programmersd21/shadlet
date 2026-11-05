---
name: design-shadlet-interfaces
description: Design responsive, accessible interfaces using Shadlet's documented components, layout primitives, themes, and examples. Use when creating or refining application screens, design systems, or component compositions.
---

# Design Shadlet interfaces

Build screens from the implemented Shadlet catalogue and responsive layout primitives; do not assume every upstream shadcn/ui component exists.

## Workflow

1. Check `docs/components/catalogue.md` and `docs/guides/layouts.md` for supported APIs. Use `Row`, `Column`, `Grid`, `Container`, `Center`, `Wrap`, and `ScrollArea` for structure before reaching for arbitrary CSS.
2. Use semantic tags through `as_` and stable fragment `id`s where appropriate. Use theme tokens and existing `class_name`/`style` escape hatches only for details the public API does not cover.
3. Give controls visible labels with `ui.Field` or an explicit accessible name. Ensure errors are associated with fields and status changes are announced.
4. Preserve focus-visible states, keyboard operation, reduced-motion preferences, responsive overflow, and both light and dark themes. Prefer real overlay/menu primitives over positioned generic boxes.
5. Compare against actual Shadlet examples and inspect desktop and narrow viewport behavior. Do not claim pixel parity with an official block unless screenshots and interactions have been checked.

## References

- `docs/guides/layouts.md`
- `docs/guides/themes.md`
- `docs/guides/components.md`
- `docs/components/catalogue.md`
- `examples/layouts/`
- `examples/components/`
