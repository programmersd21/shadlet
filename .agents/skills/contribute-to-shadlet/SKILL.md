---
name: contribute-to-shadlet
description: Make maintainable changes to the Shadlet framework itself. Use for repository architecture, compatibility, Python and TypeScript conventions, documentation, and focused regression fixes.
---

# Contribute to Shadlet

Make the smallest coherent change that fixes a demonstrated issue while preserving protocol v2 and existing public behavior where possible.

## Workflow

1. Read `CONTRIBUTING.md`, `docs/architecture/index.md`, and the owning subsystem's guide.
2. Trace the public API through Python validation/serialization, protocol, renderer, and docs before changing a cross-boundary feature.
3. Reuse existing patterns and dependencies. Avoid broad exception handling, silent fallbacks, unsafe type suppression, and unrelated refactors.
4. Add a regression test with each correctness fix. Update public docs and the component catalogue when public behavior changes.
5. Run focused checks from `docs/development/testing.md`, inspect `git diff --check` and the full diff, and state exact results. Do not claim checks that were not run.
6. Keep release operations separate: do not publish, create tags, or change protocol versions unless the task explicitly asks and the implementation requires it.

## References

- `CONTRIBUTING.md`
- `docs/architecture/index.md`
- `docs/development/testing.md`
- `docs/limitations.md`
