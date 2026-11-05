# Agent Skills

Shadlet includes a maintained set of task-specific Agent Skills for coding assistants. Each skill is a directory containing a `SKILL.md` with standard `name` and `description` frontmatter. Skills load their full instructions only when relevant, keeping repository-wide instructions short.

## Included workflows

- **Build applications**: Python app structure, reactive state, events, routes, forms, tables, and integrations.
- **Design interfaces**: responsive composition, accessibility, themes, and supported components.
- **Author components**: Python API, runtime validation, protocol, React implementation, tests, and docs.
- **Author extensions**: namespaced React components, package assets, browser bridge, and trust boundaries.
- **Debug applications**: evidence-based diagnosis across server, websocket, renderer, filesystem, and browser.
- **Contribute**: framework architecture, compatibility, and regression practices.
- **Review code**: actionable correctness, security, accessibility, and test findings.
- **Test**: Python, renderer, browser, packaging, and documentation workflows.
- **Release**: version consistency and release candidate verification.
- **Migrate**: application upgrades based on versioned compatibility guides.

See [the skill inventory](https://github.com/programmersd21/shadlet/blob/main/.agents/skills/README.md) for the host discovery notes.

## Compatibility

Canonical skills are in `.agents/skills/`, the project-level shared location documented by Codex, Cursor, Gemini CLI, and GitHub Copilot. Claude Code project discovery uses an exact `.claude/skills/` mirror. Copilot code review also has a review-focused mirror at `.github/skills/review-shadlet-code/`. Run `python tooling/validate_skills.py` to check frontmatter, repository links, expected inventory, and mirror consistency.

No skill pre-approves shell or other tools. Hosts may require skills to be enabled, a trusted workspace, or a refresh/restart after files change. Check the host's skill list when a skill does not appear.

## Keeping skills current

When a public API or workflow changes, update the relevant canonical skill and its Claude mirror; update the Copilot review mirror if the review workflow changes. Run the validator and the focused tests/docs checks. Skill instructions must defer to the source code, current docs, and explicit user directions; they must not invent API support.

Shadlet 0.6.0 skills state the verified release scope: the component set is not full upstream shadcn/ui parity, and the auth/CRUD starters are demonstrations, not production identity or durable database implementations.
