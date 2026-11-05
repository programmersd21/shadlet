---
name: migrate-shadlet
description: Migrate an application across Shadlet versions using the repository's verified migration guides and compatibility notes. Use for dependency upgrades and API or behavior changes.
---

# Migrate Shadlet applications

Use the migration guide for the exact source and target versions. Do not infer API removals from a version number.

## Workflow

1. Identify the app's current Shadlet version, Python version, and any renderer extension packages.
2. Read the matching guide in `docs/development/` and `docs/reference/compatibility.md`; inspect the implementation if the docs do not answer a concrete compatibility question.
3. Change the dependency constraint deliberately. Preserve protocol v2 unless the migration documentation or code demonstrates a required protocol transition.
4. Apply only documented API changes. For 0.5.x to 0.6.0, check `as_` serialization for `Box`, `Grid`, and `Text`; `Box`/`Grid` fragment IDs; and the 1–500 server table page-size bound.
5. Run application tests and smoke-test key pages, navigation, forms, tables, and extensions. Verify a production renderer build if custom browser assets are involved.
6. Update dependency locks and document any app-specific behavior change; do not rewrite project templates unless starting a new app.

## References

- `docs/development/migration-0.5-to-0.6.md`
- `docs/reference/compatibility.md`
- `docs/limitations.md`
