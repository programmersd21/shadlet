from __future__ import annotations

from typing import Any

import pytest
import shadlet as ui
from shadlet.runtime.sessions import SessionLimitError, SessionManager
from shadlet.web.config import WebConfig


async def _noop(_: dict[str, Any]) -> None:
    return None


def _app() -> ui.App:
    app = ui.App("manager")

    @app.page("/")
    def home(ctx: ui.Context):
        return ui.Text("ok")

    return app


@pytest.mark.anyio
async def test_manager_restores_session_by_token():
    manager = SessionManager(_app(), WebConfig())
    first = await manager.acquire(token=None, send_json=_noop)
    await first.send_init()
    second = await manager.acquire(token=first.token, send_json=_noop)
    assert second is first
    assert len(manager) == 1


@pytest.mark.anyio
async def test_manager_creates_new_session_for_unknown_token():
    manager = SessionManager(_app(), WebConfig())
    first = await manager.acquire(token=None, send_json=_noop)
    second = await manager.acquire(token="not-a-real-token", send_json=_noop)
    assert second is not first
    assert len(manager) == 2


@pytest.mark.anyio
async def test_manager_enforces_session_limit():
    manager = SessionManager(_app(), WebConfig(max_sessions=1))
    await manager.acquire(token=None, send_json=_noop)
    with pytest.raises(SessionLimitError):
        await manager.acquire(token=None, send_json=_noop)


@pytest.mark.anyio
async def test_manager_sweeps_expired_sessions(monkeypatch: pytest.MonkeyPatch):
    manager = SessionManager(_app(), WebConfig(session_ttl=0.01))
    session = await manager.acquire(token=None, send_json=_noop)
    session.detach()
    session.last_seen -= 1.0
    await manager.sweep()
    assert len(manager) == 0
    assert session.closed


@pytest.mark.anyio
async def test_manager_discard_removes_session():
    manager = SessionManager(_app(), WebConfig())
    session = await manager.acquire(token=None, send_json=_noop)
    await manager.discard(session)
    assert len(manager) == 0
    assert session.closed


@pytest.mark.anyio
async def test_manager_does_not_expire_connected_sessions():
    manager = SessionManager(_app(), WebConfig(session_ttl=0.01))
    session = await manager.acquire(token=None, send_json=_noop)
    session.last_seen -= 1.0
    await manager.sweep()
    assert len(manager) == 1
    assert not session.closed
