"""Web server runtime serving the Starlette application and WebSockets."""

from __future__ import annotations

import json
import os
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from shadlet.protocol.models import PongMessage
from shadlet.runtime.session import Session

if TYPE_CHECKING:
    from shadlet.app.app import App


def create_web_app(
    app: App,
    static_dir: str | None = None,
    reload: bool = False,
) -> Starlette:
    if static_dir is None:
        candidates = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "shadlet" / "web" / "static")  # pyright: ignore[reportAttributeAccessIssue]
        if getattr(sys, "frozen", False):
            # resources/renderer next to resources/python
            candidates.append(Path(sys.executable).parent.parent / "renderer")
        candidates.append(Path(__file__).resolve().parent / "static")
        candidates.append(
            Path(__file__).resolve().parents[4] / "packages" / "renderer" / "dist"
        )
        for cand in candidates:
            if cand.exists() and (cand / "index.html").exists():
                static_dir = str(cand)
                break

    sessions: dict[str, Session] = {}

    async def serve_index(request: Request) -> FileResponse | HTMLResponse:
        if static_dir:
            index_file = os.path.join(static_dir, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
        return HTMLResponse("<h1>shadlet</h1><p>renderer dist not found.</p>")

    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()

        async def send_json(data: dict[str, Any]) -> None:
            await websocket.send_text(json.dumps(data))

        session = Session(app, send_json=send_json)
        sessions[session.id] = session
        session.attach(send_json, platform="web")
        requested = websocket.query_params.get("path", "/")
        if requested and requested != "/":
            await session.handle_navigate(requested, seq=0)
        else:
            await session.send_init()

        try:
            while True:
                text = await websocket.receive_text()
                data = json.loads(text)
                msg_type = data.get("type")
                if msg_type == "event":
                    await session.handle_event(
                        data.get("eventId", data.get("event_id", "")),
                        data.get("payload", {}),
                        seq=data.get("seq", 1),
                        request_id=data.get("requestId", data.get("request_id")),
                    )
                elif msg_type == "navigate":
                    await session.handle_navigate(
                        data.get("path", "/"),
                        seq=data.get("seq", 1),
                    )
                elif msg_type == "ping":
                    await session.send(PongMessage(seq=data.get("seq", 0)))
        except WebSocketDisconnect:
            pass
        finally:
            await session.close()
            sessions.pop(session.id, None)

    pkg_assets = Path(__file__).resolve().parent.parent / "assets"

    routes: list[Any] = [
        WebSocketRoute("/ws", ws_endpoint),
    ]

    # Dynamic logo resolver: checks user-specified app icon first, then falls back to default
    async def serve_logo_svg(req: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon and current_icon.endswith(".svg"):
            user_path = Path(current_icon)
            if not user_path.is_absolute():
                user_path = Path.cwd() / user_path
            if user_path.exists():
                return FileResponse(str(user_path))
        if pkg_assets.exists() and (pkg_assets / "logo.svg").exists():
            return FileResponse(str(pkg_assets / "logo.svg"))
        return HTMLResponse("<svg></svg>", media_type="image/svg+xml")

    async def serve_logo_png(req: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon and current_icon.endswith(".png"):
            user_path = Path(current_icon)
            if not user_path.is_absolute():
                user_path = Path.cwd() / user_path
            if user_path.exists():
                return FileResponse(str(user_path))
        if pkg_assets.exists() and (pkg_assets / "logo.png").exists():
            return FileResponse(str(pkg_assets / "logo.png"))
        return HTMLResponse("", status_code=404)

    async def serve_app_icon(req: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon:
            user_path = Path(current_icon)
            if not user_path.is_absolute():
                user_path = Path.cwd() / user_path
            if user_path.exists():
                return FileResponse(str(user_path))
        # Default: svg then png
        if pkg_assets.exists() and (pkg_assets / "logo.svg").exists():
            return FileResponse(str(pkg_assets / "logo.svg"))
        if pkg_assets.exists() and (pkg_assets / "logo.png").exists():
            return FileResponse(str(pkg_assets / "logo.png"))
        return HTMLResponse("", status_code=404)

    routes.append(Route("/logo.svg", serve_logo_svg))
    routes.append(Route("/logo.png", serve_logo_png))
    routes.append(Route("/_app_icon", serve_app_icon))

    if pkg_assets.exists():
        routes.append(
            Mount(
                "/_shadlet_assets",
                app=StaticFiles(directory=str(pkg_assets)),
                name="shadlet_assets",
            )
        )

    if static_dir and os.path.exists(static_dir):
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.exists(assets_dir):
            routes.append(
                Mount("/assets", app=StaticFiles(directory=assets_dir), name="assets")
            )
        routes.append(Route("/{path:path}", serve_index))
    else:
        routes.append(Route("/{path:path}", serve_index))

    # --- Hot-reload setup ---
    # All reload state is local to create_web_app so there are no global mutations.
    # The watcher thread reads _loop_cell[0] after lifespan sets it, avoiding
    # the race that caused "loop is None → reload silently skipped".

    if reload:
        import asyncio
        import runpy
        import threading
        import time

        from shadlet.app.app import App as ShadletApp

        # Mutable cell shared between the lifespan coroutine and the watcher thread
        _loop_cell: list[asyncio.AbstractEventLoop | None] = [None]
        _last_reload: list[float] = [0.0]

        def _do_reload(loop: asyncio.AbstractEventLoop) -> None:
            """Re-execute main.py and push diff patches to all connected sessions."""
            main_script = Path.cwd() / "main.py"
            new_app: ShadletApp | None = None
            if main_script.exists():
                try:
                    res = runpy.run_path(str(main_script))
                    for val in res.values():
                        if isinstance(val, ShadletApp):
                            new_app = val
                            break
                except Exception as error:  # noqa: BLE001
                    print(
                        f"[shadlet] reload failed executing main.py: {error}",
                        flush=True,
                    )
                    return

            if new_app is not None:
                app.title = new_app.title
                app.icon = new_app.icon
                app._routes = new_app._routes
                app._not_found = new_app._not_found

            for session in list(sessions.values()):
                if new_app is not None:
                    session.app = new_app
                    session.route = new_app.match(session.route.path)
                asyncio.run_coroutine_threadsafe(session.refresh(), loop)

        def _watch() -> None:
            import watchfiles

            # Block until the asyncio event loop is running (set by lifespan)
            for _ in range(100):
                if _loop_cell[0] is not None:
                    break
                time.sleep(0.05)

            loop = _loop_cell[0]
            if loop is None:
                print(
                    "[shadlet] watcher: event loop never started, hot reload disabled",
                    flush=True,
                )
                return

            print("[shadlet] watcher started", flush=True)
            for _ in watchfiles.watch(
                str(Path.cwd()),
                watch_filter=watchfiles.PythonFilter(),
            ):
                now = time.monotonic()
                if now - _last_reload[0] < 0.3:
                    continue
                _last_reload[0] = now
                print("[shadlet] change detected, reloading", flush=True)
                _do_reload(loop)

        @asynccontextmanager
        async def _lifespan(app_: Any):
            # Capture the running loop FIRST, then start the watcher thread
            _loop_cell[0] = asyncio.get_running_loop()
            threading.Thread(target=_watch, daemon=True).start()
            yield
            _loop_cell[0] = None

        return Starlette(routes=routes, lifespan=_lifespan)

    # Serve project assets if present
    assets_dir = os.environ.get("SHADLET_ASSETS_DIR") or str(Path.cwd() / "assets")
    if Path(assets_dir).exists():
        from starlette.routing import Mount as _Mount
        from starlette.staticfiles import StaticFiles as _StaticFiles

        routes.insert(
            0,
            _Mount(
                "/assets", app=_StaticFiles(directory=assets_dir), name="project_assets"
            ),
        )

    return Starlette(routes=routes)


def find_available_port(
    host: str = "127.0.0.1", start_port: int = 8000, max_attempts: int = 100
) -> int:
    """Find an available TCP port starting from ``start_port``."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            continue
    raise OSError(
        f"Could not find an available port in range {start_port}-{start_port + max_attempts} on {host}"
    )


def run_app(
    app: App,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
) -> None:
    actual_port = find_available_port(host, port)
    if actual_port != port:
        print(
            f"[shadlet] Port {port} is in use; automatically switched to port {actual_port}."
        )

    if not reload:
        reload = os.environ.get("SHADLET_RELOAD", "").lower() in {"1", "true", "yes"}
    starlette_app = create_web_app(app, reload=reload)
    uvicorn.run(starlette_app, host=host, port=actual_port, reload=False)


__all__ = ["create_web_app", "find_available_port", "run_app"]
