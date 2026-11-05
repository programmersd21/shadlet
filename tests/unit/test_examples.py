import asyncio
import runpy
from pathlib import Path

import pytest
from shadlet.runtime.session import Session

EXAMPLES = (
    "background-tasks",
    "charts",
    "components",
    "counter",
    "dashboard",
    "data-table",
    "deployment",
    "forms",
    "icons-demo",
    "layouts",
    "routing",
    "storage",
    "todo",
    "uploads",
)


@pytest.mark.parametrize("example", EXAMPLES)
def test_example_home_page_serializes(example: str) -> None:
    app_path = Path("examples") / example / "main.py"
    app = runpy.run_path(str(app_path))["app"]
    messages: list[dict[str, object]] = []

    async def send_json(message: dict[str, object]) -> None:
        messages.append(message)

    async def render() -> None:
        session = Session(app, send_json=send_json)
        await session.send_init()
        assert len(messages) == 1
        assert messages[0]["type"] == "init"
        tree = messages[0]["tree"]
        assert isinstance(tree, dict)
        assert tree["type"] in {"Box", "Center", "Column", "Row"}
        await session.close()

    asyncio.run(render())
