import importlib.util
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPOSITORY / "tooling" / "compatibility" / "generate_matrix.py"
SPEC = importlib.util.spec_from_file_location("generate_matrix", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def test_compatibility_matrix_matches_sources() -> None:
    assert GENERATOR.main(["--check"]) == 0


def test_compatibility_matrix_covers_every_pinned_upstream_component() -> None:
    matrix = GENERATOR.build_matrix()
    missing = {
        entry["upstream"]
        for entry in matrix["components"]
        if entry["status"] == "missing"
    }
    assert missing == set()
    assert matrix["counts"]["upstream_total"] == 56
    types = {entry["upstream"]: entry["shadlet_type"] for entry in matrix["components"]}
    assert types["scroll-area"] == "ScrollArea"
    assert types["direction"] == "Direction"
    assert types["toast"] == "Toast"
    assert types["sonner"] == "Toast"
