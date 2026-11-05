# Repository guidance

Use `.agents/skills/` for task-specific Shadlet workflows. Read the matching `SKILL.md` before application, component, extension, debugging, review, testing, migration, or release work. `.claude/skills/` mirrors are validated against that canonical directory.

Use the documented APIs and verified scope in `docs/`; Shadlet 0.6.0 does not promise full shadcn/ui catalogue parity. Keep Python, protocol, and renderer contracts aligned. Add a regression test for behavior changes and update public documentation. Never claim checks that were not run.
