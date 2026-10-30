from typing import Any

import pytest
import shadlet as ui
from shadlet.runtime.session import Session


@pytest.mark.asyncio
async def test_multi_session_concurrency_and_isolation():
    """Verify that multiple concurrent sessions maintain isolated state without cross-talk."""
    app = ui.App(title="Multi-Session Test App")

    @app.page("/")
    def page(ctx: ui.Context):
        val = ctx.state("initial", key="user_val")
        return ui.Column(ui.Text(f"State: {val.value}"))

    session_a_messages = []
    session_b_messages = []

    async def send_a(msg: dict[str, Any]):
        session_a_messages.append(msg)

    async def send_b(msg: dict[str, Any]):
        session_b_messages.append(msg)

    session_a = Session(app, send_json=send_a, platform="web")
    session_b = Session(app, send_json=send_b, platform="web")

    # Connect both sessions
    await session_a.send_init()
    await session_b.send_init()

    assert len(session_a_messages) == 1
    assert len(session_b_messages) == 1
    assert session_a_messages[0]["type"] == "init"
    assert session_b_messages[0]["type"] == "init"

    # Mutate Session A's state slot
    state_a = session_a.state_store.get(
        "/:user_val", "initial", session_a.state_changed
    )
    state_a.value = "mutated_in_session_a"
    await session_a.flush()

    # Session A receives update patch
    assert len(session_a_messages) == 2
    assert session_a_messages[1]["type"] == "update"
    assert "mutated_in_session_a" in str(session_a_messages[1])

    # Session B should remain untouched
    assert len(session_b_messages) == 1
    state_b = session_b.state_store.get(
        "/:user_val", "initial", session_b.state_changed
    )
    assert state_b.value == "initial"

    # Close sessions cleanly
    await session_a.close()
    await session_b.close()


@pytest.mark.asyncio
async def test_session_reconnection_and_backpressure():
    """Verify that session handles disconnect, re-connection and queued toasts/events."""
    app = ui.App(title="Reconnection App")

    @app.page("/")
    def page(ctx: ui.Context):
        return ui.Column(ui.Button("Action"))

    received = []

    async def send(msg: dict[str, Any]):
        received.append(msg)

    session = Session(app, send_json=send, platform="web")
    await session.send_init()
    assert len(received) == 1
    assert session.connected

    # Detach (simulate client connection loss)
    session.detach()
    assert not session.connected

    # Send toast while disconnected (must be queued safely in _toast_queue)
    ctx = ui.Context(session, session.route)
    ctx.toast("Important offline notification", description="Buffered")

    assert len(session._toast_queue) == 1
    assert session._toast_queue[0].message == "Important offline notification"

    # Re-attach client
    new_received = []

    async def new_send(msg: dict[str, Any]):
        new_received.append(msg)

    session.attach(new_send, platform="web")
    assert session.connected

    # Clean up
    await session.close()
