"""Reproducible, informational microbenchmarks for core Shadlet workloads."""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import statistics
import time
from collections.abc import Awaitable, Callable
from typing import Any

import shadlet as ui
from shadlet.events.registry import EventRegistry
from shadlet.events.types import ClickEvent
from shadlet.protocol.models import Node
from shadlet.runtime.diff import diff_trees
from shadlet.runtime.render import serialize_component
from shadlet.runtime.session import Session

ROW_COUNT = 10_000
TREE_SIZE = 1_000
CONCURRENT_SESSIONS = 50


class _RenderContext:
    def __init__(self) -> None:
        self.event_registry = EventRegistry()


def _ignore_click(event: ui.ClickEvent) -> None:
    del event


def _measure(
    function: Callable[[], Any], *, iterations: int, warmups: int
) -> dict[str, float]:
    for _ in range(warmups):
        function()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        function()
        samples.append(time.perf_counter() - start)
    median_ms = statistics.median(samples) * 1000
    return {
        "median_ms": round(median_ms, 3),
        "operations_per_second": round(1000 / median_ms, 2) if median_ms else 0,
    }


async def _measure_async(
    function: Callable[[], Awaitable[object]], *, iterations: int, warmups: int
) -> dict[str, float]:
    for _ in range(warmups):
        await function()
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await function()
        samples.append(time.perf_counter() - start)
    median_ms = statistics.median(samples) * 1000
    return {
        "median_ms": round(median_ms, 3),
        "operations_per_second": round(1000 / median_ms, 2) if median_ms else 0,
    }


async def _measure_concurrent_sessions(
    *, iterations: int, warmups: int
) -> dict[str, float]:
    app = ui.App("session benchmark")

    @app.page("/")
    def home(ctx: ui.Context) -> ui.Component:
        count = ctx.state(0, key="benchmark-count")

        def increment(event: ClickEvent) -> None:
            del event
            count.value += 1

        return ui.Button(str(count.value), on_click=increment)

    sessions: list[Session] = []
    event_ids: list[str] = []
    messages: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    try:
        for _ in range(CONCURRENT_SESSIONS):
            session = Session(app, send_json=send)
            await session.send_init()
            event_ids.append(messages[-1]["tree"]["events"]["click"])
            sessions.append(session)
        sequence = 0

        async def update_sessions() -> None:
            nonlocal sequence
            sequence += 1
            await asyncio.gather(
                *(
                    session.handle_event(event_id, {}, seq=sequence)
                    for session, event_id in zip(sessions, event_ids, strict=True)
                )
            )

        return await _measure_async(
            update_sessions, iterations=iterations, warmups=warmups
        )
    finally:
        await asyncio.gather(*(session.close() for session in sessions))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.iterations < 1 or arguments.warmups < 0:
        parser.error("--iterations must be positive and --warmups non-negative")

    rows = [
        {"id": index, "name": f"user-{index:05}", "group": f"group-{index % 8}"}
        for index in range(ROW_COUNT)
    ]
    columns = [
        {"key": "id", "header": "id"},
        {"key": "name", "header": "name"},
        {"key": "group", "header": "group"},
    ]
    component = ui.Column(
        *(
            ui.Button(f"row {index}", on_click=_ignore_click)
            for index in range(TREE_SIZE)
        )
    )
    context = _RenderContext()
    tree = serialize_component(component, context)
    changed_tree = tree.model_copy(deep=True)
    changed_tree.children[-1] = Node(
        id=changed_tree.children[-1].id,
        type="#text",
        text="changed",
    )
    search_term = "user-09"
    concurrent_result = asyncio.run(
        _measure_concurrent_sessions(
            iterations=arguments.iterations,
            warmups=arguments.warmups,
        )
    )

    results = {
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "row_count": ROW_COUNT,
            "tree_nodes": TREE_SIZE + 1,
            "concurrent_sessions": CONCURRENT_SESSIONS,
            "iterations": arguments.iterations,
            "warmups": arguments.warmups,
        },
        "benchmarks": {
            "datatable_construct_10k": _measure(
                lambda: ui.DataTable(columns, rows, row_key="id"),
                iterations=arguments.iterations,
                warmups=arguments.warmups,
            ),
            "serialize_tree_1k": _measure(
                lambda: serialize_component(component, context),
                iterations=arguments.iterations,
                warmups=arguments.warmups,
            ),
            "diff_tree_1k": _measure(
                lambda: diff_trees(tree, changed_tree),
                iterations=arguments.iterations,
                warmups=arguments.warmups,
            ),
            "protocol_json_1k": _measure(
                lambda: tree.model_dump_json(),
                iterations=arguments.iterations,
                warmups=arguments.warmups,
            ),
            "filter_sort_10k": _measure(
                lambda: sorted(
                    (row for row in rows if search_term in row["name"]),
                    key=lambda row: row["id"],
                    reverse=True,
                ),
                iterations=arguments.iterations,
                warmups=arguments.warmups,
            ),
            "concurrent_session_updates_50": concurrent_result,
        },
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
