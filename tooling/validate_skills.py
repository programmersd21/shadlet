from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOTS = (Path(".agents/skills"), Path(".claude/skills"))
SKILL_NAMES = {
    "build-shadlet-apps",
    "design-shadlet-interfaces",
    "author-shadlet-components",
    "author-shadlet-extensions",
    "debug-shadlet-apps",
    "contribute-to-shadlet",
    "review-shadlet-code",
    "test-shadlet",
    "release-shadlet",
    "migrate-shadlet",
}


def _read_skill(path: Path, repository: Path) -> tuple[str, list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return "", [f"{path}: cannot read skill: {error}"]

    if not text.startswith("---\n"):
        errors.append(f"{path}: YAML frontmatter must start at byte zero")
        return text, errors

    end = text.find("\n---\n", 4)
    if end < 0:
        errors.append(f"{path}: missing closing frontmatter delimiter")
        return text, errors

    frontmatter = text[4:end]
    name = re.search(r"^name:\s*([a-z0-9][a-z0-9-]*)\s*$", frontmatter, re.MULTILINE)
    description = re.search(r"^description:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if name is None:
        errors.append(f"{path}: missing or invalid name field")
    elif name.group(1) != path.parent.name:
        errors.append(f"{path}: name does not match directory {path.parent.name!r}")
    if description is None:
        errors.append(f"{path}: missing description field")
    elif len(description.group(1)) > 1024:
        errors.append(f"{path}: description exceeds 1024 characters")

    body = text[end + 5 :]
    if body.count("```") % 2:
        errors.append(f"{path}: unclosed fenced code block")

    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if target.startswith(("https://", "http://", "#", "mailto:")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(repository.resolve())
        except ValueError:
            errors.append(f"{path}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{path}: broken repository link: {target}")

    return text, errors


def validate(repository: Path) -> list[str]:
    errors: list[str] = []
    canonical = repository / SKILL_ROOTS[0]
    found = {path.parent.name for path in canonical.glob("*/SKILL.md")}
    if found != SKILL_NAMES:
        errors.append(
            f"{canonical}: skill set mismatch; missing={sorted(SKILL_NAMES - found)}, "
            f"unexpected={sorted(found - SKILL_NAMES)}"
        )

    canonical_text: dict[str, str] = {}
    for name in sorted(SKILL_NAMES):
        path = canonical / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"{path}: missing SKILL.md")
            continue
        text, skill_errors = _read_skill(path, repository)
        canonical_text[name] = text
        errors.extend(skill_errors)

    for root in SKILL_ROOTS[1:]:
        for name, text in canonical_text.items():
            mirror = repository / root / name / "SKILL.md"
            if not mirror.is_file():
                errors.append(f"{mirror}: missing mirror")
                continue
            try:
                mirror_text = mirror.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                errors.append(f"{mirror}: cannot read mirror: {error}")
                continue
            if mirror_text != text:
                errors.append(f"{mirror}: differs from canonical .agents skill")

    copilot_review = repository / ".github/skills/review-shadlet-code/SKILL.md"
    if not copilot_review.is_file():
        errors.append(f"{copilot_review}: missing Copilot code-review skill")
    elif canonical_text.get("review-shadlet-code"):
        try:
            if (
                copilot_review.read_text(encoding="utf-8")
                != canonical_text["review-shadlet-code"]
            ):
                errors.append(f"{copilot_review}: differs from canonical .agents skill")
        except (OSError, UnicodeError) as error:
            errors.append(f"{copilot_review}: cannot read skill: {error}")

    return errors


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    errors = validate(repository)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(SKILL_NAMES)} Shadlet skills and provider mirrors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
