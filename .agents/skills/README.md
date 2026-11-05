# Shadlet Agent Skills

The canonical skills live in `.agents/skills/` and use the Agent Skills `SKILL.md` format. Claude Code project skills are mirrored in `.claude/skills/`; the Copilot code-review skill is also mirrored in `.github/skills/review-shadlet-code/`. Mirrors are byte-checked by `python tooling/validate_skills.py`. Edit the canonical `.agents/skills/` copy first, then update both mirrors.

| Skill | Use it for |
| --- | --- |
| `build-shadlet-apps` | Python app structure, state, events, forms, tables, and runtime integrations |
| `design-shadlet-interfaces` | Responsive and accessible Shadlet UI composition |
| `author-shadlet-components` | Built-in Python/React component and protocol work |
| `author-shadlet-extensions` | Packaged React extensions and their Python assets |
| `debug-shadlet-apps` | Runtime, browser, protocol, filesystem, and pytest failures |
| `contribute-to-shadlet` | Framework contributions and compatibility practices |
| `review-shadlet-code` | Evidence-based change and pull-request review |
| `test-shadlet` | Python, renderer, browser, packaging, and docs verification |
| `release-shadlet` | Release candidate preparation and distribution checks |
| `migrate-shadlet` | Version upgrades using verified migration notes |

## Supported hosts

The shared `.agents/skills/` location is documented for Codex, Cursor, Gemini CLI, and GitHub Copilot. Claude Code uses the matching `.claude/skills/` mirror. GitHub Copilot code review also receives a review-focused copy in `.github/skills/`. Host versions and product surfaces can differ; confirm discovery in the host's skills list or UI. The files use required `name` and `description` frontmatter and avoid host-specific tool permissions.

These instructions describe Shadlet 0.6.0 as implemented. The component catalogue is not complete upstream shadcn/ui parity; auth and CRUD templates are demonstrations rather than production identity or database layers.
