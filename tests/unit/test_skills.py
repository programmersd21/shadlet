import importlib.util
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPOSITORY / "tooling" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_agent_skills_have_valid_metadata_links_and_provider_mirrors() -> None:
    assert VALIDATOR.validate(REPOSITORY) == []
    assert len(VALIDATOR.SKILL_NAMES) == 10
