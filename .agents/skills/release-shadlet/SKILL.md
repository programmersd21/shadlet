---
name: release-shadlet
description: Prepare and verify a Shadlet release without publishing or tagging unless explicitly authorized. Use for version consistency, changelog, checks, builds, package inspection, and release notes.
---

# Prepare a Shadlet release

Prepare a reviewable release candidate. This skill does not authorize publishing or tagging.

## Workflow

1. Read `docs/development/releases.md`, the latest migration guide, `docs/limitations.md`, and the current changelog.
2. Verify the source-of-truth version in `packages/python/shadlet/version.py` and compare packaging metadata, renderer metadata/lockfile, templates, protocol fixtures if versioned, and docs.
3. Update the changelog with verified changes only. Add migration instructions for public behavior changes; keep documented limitations accurate.
4. Run the checks that apply, including Python tests, renderer lint/typecheck/tests/build, strict MkDocs build, and distribution builds. Do not replace failing checks with claims.
5. Inspect wheel and sdist contents and verify a clean wheel installation includes renderer assets and templates. Keep Node.js maintainer-only unless the installed runtime actually requires it.
6. Review `git diff`, package version references, licenses, and release notes. Record exact test commands and results.
7. Stop before publishing to PyPI, creating a GitHub release/tag, or pushing a release tag unless the maintainer explicitly authorized that operation.

## References

- `docs/development/releases.md`
- `docs/development/testing.md`
- `docs/development/migration-0.5-to-0.6.md`
- `CHANGELOG.md`
- `pyproject.toml`
