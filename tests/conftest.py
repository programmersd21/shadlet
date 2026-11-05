from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4


def pytest_configure(config) -> None:
    """Give each pytest process its own writable temporary directory."""
    if config.getoption("basetemp") is not None:
        return

    temporary_root = Path(gettempdir())
    candidate = temporary_root / f"shadlet-pytest-{uuid4().hex}"
    try:
        candidate.mkdir()
    except OSError:
        candidate = config.rootpath / f".pytest-run-{uuid4().hex}"
        candidate.mkdir()
    config.option.basetemp = str(candidate)
