"""Web server runtime serving the Starlette application and WebSockets."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import mimetypes
import os
import socket
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import uvicorn
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.formparsers import MultiPartException
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.types import Message
from starlette.websockets import WebSocket, WebSocketDisconnect

from shadlet.app.uploads import UploadedFile, UploadRequest
from shadlet.protocol.models import (
    ErrorMessage,
    EventMessage,
    HelloMessage,
    NavigateMessage,
    PingMessage,
    PongMessage,
)
from shadlet.protocol.validation import parse_client_message
from shadlet.protocol.version import SUPPORTED_PROTOCOL_VERSIONS, negotiate_protocol
from shadlet.runtime.sessions import SessionLimitError, SessionManager
from shadlet.web.config import ConnectionRequest

if TYPE_CHECKING:
    from shadlet.app.app import App

logger = logging.getLogger("shadlet.web")

_LOCAL_ORIGIN_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _static_directory() -> str | None:
    candidates = [
        Path(__file__).resolve().parent / "static",
        Path(__file__).resolve().parents[4] / "packages" / "renderer" / "dist",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "index.html").is_file():
            return str(candidate)
    return None


def _origin_allowed(websocket: WebSocket, app: App) -> bool:
    return _origin_is_allowed(
        websocket.headers.get("origin"), websocket.headers.get("host"), app
    )


def _origin_is_allowed(origin: str | None, host: str | None, app: App) -> bool:
    allowed = app.web.allowed_origins
    if allowed is not None:
        if "*" in allowed:
            return True
        if origin is None:
            return False
        normalised = origin.rstrip("/").lower()
        return any(normalised == candidate.rstrip("/").lower() for candidate in allowed)
    if origin is None:
        return True
    parsed = urlsplit(origin)
    if host and parsed.netloc.lower() == host.lower():
        return True
    return (parsed.hostname or "").lower() in _LOCAL_ORIGIN_HOSTS


def _configured_icon_path(
    icon: str | None,
    *,
    asset_root: Path,
    package_assets: Path,
) -> Path | None:
    if not icon:
        return None
    try:
        parsed = urlsplit(icon)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc:
        return None

    raw_path = Path(icon)
    candidates = (
        [raw_path]
        if raw_path.is_absolute()
        else [
            Path.cwd() / raw_path,
            asset_root / raw_path,
        ]
    )
    roots = (asset_root.resolve(), package_assets.resolve())
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if not resolved.is_file():
            continue
        if any(resolved.is_relative_to(root) for root in roots):
            return resolved
    return None


async def _authenticate(websocket: WebSocket, app: App, hello: HelloMessage) -> bool:
    authenticator = app.authenticate
    if authenticator is None:
        return True
    request = ConnectionRequest(
        origin=websocket.headers.get("origin"),
        host=websocket.headers.get("host"),
        path=hello.path,
        token=hello.token,
        headers=dict(websocket.headers.items()),
        query=dict(websocket.query_params),
    )
    result = authenticator(request)
    if inspect.isawaitable(result):
        result = await result
    return bool(result)


def _error_payload(code: str, message: str, *, fatal: bool = False) -> dict[str, Any]:
    return ErrorMessage(code=code, message=message, fatal=fatal).model_dump(mode="json")


async def _close_with_error(
    websocket: WebSocket, code: str, message: str, *, close_code: int = 1008
) -> None:
    try:
        await websocket.send_text(json.dumps(_error_payload(code, message, fatal=True)))
        await websocket.close(code=close_code)
    except RuntimeError:
        pass


def create_web_app(
    app: App,
    static_dir: str | None = None,
    reload: bool = False,
) -> Starlette:
    app.discover_extensions()
    if static_dir is None:
        static_dir = _static_directory()

    config = app.web
    sessions = SessionManager(app, config)
    logger.debug("serving renderer assets from %s", static_dir or "embedded fallback")

    async def serve_index(request: Request) -> FileResponse | HTMLResponse:
        if static_dir:
            index_file = os.path.join(static_dir, "index.html")
            if os.path.exists(index_file):
                return FileResponse(
                    index_file,
                    headers={"Cache-Control": "no-store"},
                )
        return HTMLResponse(
            "<h1>shadlet</h1><p>renderer bundle not found; "
            "install a release wheel or run the renderer build.</p>",
            status_code=503,
        )

    async def ws_endpoint(websocket: WebSocket) -> None:
        if not _origin_allowed(websocket, app):
            await websocket.close(code=1008)
            return

        await websocket.accept()
        session = None
        generation: int | None = None
        try:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(), timeout=config.handshake_timeout
                )
            except TimeoutError:
                await _close_with_error(
                    websocket, "handshake_timeout", "handshake timed out"
                )
                return

            if len(raw.encode("utf-8")) > config.max_message_bytes:
                await _close_with_error(
                    websocket,
                    "message_too_large",
                    "handshake exceeds size limit",
                    close_code=1009,
                )
                return

            try:
                hello = HelloMessage.model_validate_json(raw)
            except ValidationError:
                await _close_with_error(
                    websocket,
                    "invalid_handshake",
                    "the first message must be a valid hello",
                )
                return

            try:
                negotiated = negotiate_protocol(hello.protocol_min, hello.protocol_max)
            except Exception:  # noqa: BLE001
                await _close_with_error(
                    websocket,
                    "protocol_incompatible",
                    f"server supports protocol {', '.join(str(v) for v in SUPPORTED_PROTOCOL_VERSIONS)}",
                )
                return

            try:
                accepted = await _authenticate(websocket, app, hello)
            except Exception:
                logger.exception("connection authenticator raised")
                await _close_with_error(
                    websocket, "authentication_error", "connection rejected"
                )
                return
            if not accepted:
                await _close_with_error(
                    websocket, "unauthorized", "connection rejected", close_code=1008
                )
                return

            async def send_json(data: dict[str, Any]) -> None:
                await websocket.send_text(
                    json.dumps(data, separators=(",", ":"), ensure_ascii=False)
                )

            try:
                session = await sessions.acquire(
                    token=hello.token,
                    send_json=send_json,
                    platform=hello.platform,
                )
            except SessionLimitError:
                await _close_with_error(
                    websocket,
                    "session_limit",
                    "server is at capacity; try again shortly",
                    close_code=1013,
                )
                return

            generation = session.generation
            await session.start(hello.path, protocol=negotiated.version)

            while True:
                raw = await websocket.receive_text()
                if len(raw.encode("utf-8")) > config.max_message_bytes:
                    await _close_with_error(
                        websocket,
                        "message_too_large",
                        "message exceeds size limit",
                        close_code=1009,
                    )
                    return
                if (
                    session is None
                    or generation is None
                    or not session.is_current(generation)
                ):
                    return
                try:
                    message = parse_client_message(json.loads(raw))
                except (json.JSONDecodeError, ValidationError):
                    if not session.allow_message():
                        await websocket.close(code=1008)
                        return
                    await session.send(
                        ErrorMessage(
                            code="invalid_message",
                            message="message failed protocol validation",
                        )
                    )
                    continue

                session.touch()
                if isinstance(message, EventMessage):
                    await session.handle_event(
                        message.event_id,
                        message.payload,
                        seq=message.seq,
                        request_id=message.request_id,
                    )
                elif isinstance(message, NavigateMessage):
                    if not session.allow_message():
                        await session.send(
                            ErrorMessage(
                                code="rate_limited",
                                message="message rate limit exceeded; slow down or reconnect",
                            )
                        )
                        continue
                    await session.handle_navigate(
                        message.path, seq=message.seq, replace=message.replace
                    )
                elif isinstance(message, PingMessage):
                    if not session.allow_message():
                        await session.send(
                            ErrorMessage(
                                code="rate_limited",
                                message="message rate limit exceeded; slow down or reconnect",
                            )
                        )
                        continue
                    await session.send(PongMessage(seq=message.seq))
                elif isinstance(message, HelloMessage):
                    if not session.allow_message():
                        await websocket.close(code=1008)
                        return
                    await session.send(
                        ErrorMessage(
                            code="unexpected_hello",
                            message="hello is only valid as the first message",
                        )
                    )
        except WebSocketDisconnect:
            pass
        except RuntimeError:
            pass
        finally:
            if (
                session is not None
                and generation is not None
                and session.is_current(generation)
            ):
                sessions.release(session)

    pkg_assets = Path(__file__).resolve().parent.parent / "assets"
    project_assets = Path(os.environ.get("SHADLET_ASSETS_DIR") or Path.cwd() / "assets")

    async def serve_logo_svg(request: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon and current_icon.endswith(".svg"):
            icon_path = _configured_icon_path(
                current_icon, asset_root=project_assets, package_assets=pkg_assets
            )
            if icon_path is not None:
                return FileResponse(str(icon_path))
        if (pkg_assets / "logo.svg").exists():
            return FileResponse(str(pkg_assets / "logo.svg"))
        return HTMLResponse("<svg></svg>", media_type="image/svg+xml")

    async def serve_logo_png(request: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon and current_icon.endswith(".png"):
            icon_path = _configured_icon_path(
                current_icon, asset_root=project_assets, package_assets=pkg_assets
            )
            if icon_path is not None:
                return FileResponse(str(icon_path))
        if (pkg_assets / "logo.png").exists():
            return FileResponse(str(pkg_assets / "logo.png"))
        return HTMLResponse("", status_code=404)

    async def serve_app_icon(request: Request) -> FileResponse | HTMLResponse:
        current_icon = app.icon
        if current_icon:
            icon_path = _configured_icon_path(
                current_icon, asset_root=project_assets, package_assets=pkg_assets
            )
            if icon_path is not None:
                return FileResponse(str(icon_path))
        if (pkg_assets / "logo.svg").exists():
            return FileResponse(str(pkg_assets / "logo.svg"))
        if (pkg_assets / "logo.png").exists():
            return FileResponse(str(pkg_assets / "logo.png"))
        return HTMLResponse("", status_code=404)

    async def serve_health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def serve_upload(request: Request) -> Response:
        upload_route = next(
            (route for route in app._upload_routes if route.path == request.url.path),
            None,
        )
        if upload_route is None:
            return JSONResponse({"error": "upload endpoint not found"}, status_code=404)
        limit = min(
            upload_route.max_bytes or config.max_upload_bytes, config.max_upload_bytes
        )
        if not _origin_is_allowed(
            request.headers.get("origin"), request.headers.get("host"), app
        ):
            return JSONResponse({"error": "origin rejected"}, status_code=403)
        if app.authenticate is not None:
            authorization = request.headers.get("authorization", "")
            token = (
                authorization[7:]
                if authorization.lower().startswith("bearer ")
                else None
            )
            auth_request = ConnectionRequest(
                origin=request.headers.get("origin"),
                host=request.headers.get("host"),
                path=request.url.path,
                token=token,
                headers=dict(request.headers.items()),
                query=dict(request.query_params),
            )
            try:
                accepted = app.authenticate(auth_request)
                if inspect.isawaitable(accepted):
                    accepted = await accepted
            except Exception:
                logger.exception("http upload authenticator raised")
                return JSONResponse(
                    {"error": "upload authentication failed"}, status_code=500
                )
            if not accepted:
                return JSONResponse({"error": "upload rejected"}, status_code=401)

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                body_size = int(content_length)
            except ValueError:
                return JSONResponse(
                    {"error": "invalid content length"}, status_code=400
                )
            if body_size > limit + 65_536:
                return JSONResponse(
                    {"error": "upload exceeds size limit"}, status_code=413
                )

        files: dict[str, list[UploadedFile]] = {}
        fields: dict[str, str] = {}
        total_size = 0

        class UploadTooLarge(Exception):
            pass

        body_size = 0

        async def bounded_receive() -> Message:
            nonlocal body_size
            message = await request.receive()
            if message["type"] == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > limit + 65_536:
                    raise UploadTooLarge
            return message

        bounded_request = Request(request.scope, bounded_receive)
        try:
            async with bounded_request.form() as form:
                for name, value in form.multi_items():
                    if isinstance(value, StarletteUploadFile):
                        data = await value.read(limit - total_size + 1)
                        total_size += len(data)
                        if total_size > limit:
                            return JSONResponse(
                                {"error": "upload exceeds size limit"}, status_code=413
                            )
                        files.setdefault(name, []).append(
                            UploadedFile(
                                filename=value.filename or "",
                                content_type=value.content_type,
                                data=data,
                            )
                        )
                    else:
                        fields[name] = value
        except (
            MultiPartException,
            ValueError,
            UnicodeDecodeError,
            AssertionError,
        ) as error:
            logger.info("invalid multipart upload: %s", error)
            return JSONResponse({"error": "invalid multipart upload"}, status_code=400)
        except UploadTooLarge:
            return JSONResponse({"error": "upload exceeds size limit"}, status_code=413)

        try:
            result = upload_route.handler(
                UploadRequest(
                    fields=fields,
                    files={name: tuple(items) for name, items in files.items()},
                )
            )
            if inspect.isawaitable(result):
                result = await result
        except Exception:
            logger.exception("upload handler failed for %s", upload_route.path)
            return JSONResponse({"error": "upload processing failed"}, status_code=500)
        if isinstance(result, Response):
            return result
        return JSONResponse(result)

    async def serve_extension_asset(request: Request) -> Response:
        name = request.path_params["name"]
        path = request.path_params["asset"]
        extension = app._extensions.get(name)
        if extension is None:
            return JSONResponse({"error": "extension asset not found"}, status_code=404)
        try:
            content = extension.read_asset(path)
        except (FileNotFoundError, ValueError):
            return JSONResponse({"error": "extension asset not found"}, status_code=404)
        media_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        return Response(
            content, media_type=media_type, headers={"Cache-Control": "no-cache"}
        )

    routes: list[Any] = [
        WebSocketRoute("/ws", ws_endpoint),
        Route("/healthz", serve_health, methods=["GET"]),
        Route(
            "/_shadlet_extensions/{name:str}/{asset:path}",
            serve_extension_asset,
            methods=["GET", "HEAD"],
        ),
        Route("/logo.svg", serve_logo_svg),
        Route("/logo.png", serve_logo_png),
        Route("/_app_icon", serve_app_icon),
    ]
    routes.extend(
        Route(route.path, serve_upload, methods=["POST"])
        for route in app._upload_routes
    )

    if static_dir and os.path.isdir(static_dir):
        routes.append(
            Mount(
                "/_shadlet_assets",
                app=StaticFiles(directory=static_dir),
                name="renderer_assets",
            )
        )

    if os.path.isdir(project_assets):
        routes.append(
            Mount(
                "/assets",
                app=StaticFiles(directory=str(project_assets)),
                name="project_assets",
            )
        )

    routes.append(Route("/{path:path}", serve_index))

    stop_event = threading.Event()

    @asynccontextmanager
    async def _sweep_lifespan(starlette_app: Any):
        async def _sweep() -> None:
            while True:
                await asyncio.sleep(config.sweep_interval)
                await sessions.sweep()

        sweep_task = asyncio.create_task(_sweep())
        try:
            yield
        finally:
            stop_event.set()
            sweep_task.cancel()
            await asyncio.gather(sweep_task, return_exceptions=True)
            await sessions.close_all()

    if not reload:
        return Starlette(routes=routes, lifespan=_sweep_lifespan)

    from shadlet.app.app import App as ShadletApp

    loop_cell: list[asyncio.AbstractEventLoop | None] = [None]
    last_reload: list[float] = [0.0]

    def _do_reload(loop: asyncio.AbstractEventLoop) -> None:
        main_script = Path.cwd() / "main.py"
        new_app: ShadletApp | None = None
        if main_script.exists():
            import runpy

            try:
                result = runpy.run_path(str(main_script))
                for value in result.values():
                    if isinstance(value, ShadletApp):
                        new_app = value
                        break
            except Exception:
                logger.exception("reload failed executing main.py")
                return

        if new_app is not None:
            app.title = new_app.title
            app.icon = new_app.icon
            app.theme = new_app.theme
            app.version = new_app.version
            app.debug = new_app.debug
            app.toaster = new_app.toaster
            app.web = new_app.web
            app.authenticate = new_app.authenticate
            app._routes = new_app._routes
            app._upload_routes = new_app._upload_routes
            app._extensions = new_app._extensions
            app._extensions_discovered = new_app._extensions_discovered
            app._not_found = new_app._not_found

        for session in sessions.all():
            if new_app is not None:
                session.app = new_app
                try:
                    session.route = new_app.match(session.route.path)
                except Exception:
                    logger.exception("reload failed to match session route")
                    continue
            try:
                asyncio.run_coroutine_threadsafe(session.refresh(), loop)
            except RuntimeError:
                logger.exception("reload could not schedule session refresh")

    def _watch() -> None:
        import watchfiles

        for _ in range(100):
            if loop_cell[0] is not None:
                break
            time.sleep(0.05)

        loop = loop_cell[0]
        if loop is None:
            logger.warning("watcher: event loop never started, hot reload disabled")
            return

        logger.debug("watcher started")
        for _ in watchfiles.watch(
            str(Path.cwd()),
            watch_filter=watchfiles.PythonFilter(),
            stop_event=stop_event,
        ):
            if stop_event.is_set():
                return
            now = time.monotonic()
            if now - last_reload[0] < 0.3:
                continue
            last_reload[0] = now
            logger.debug("change detected, reloading")
            _do_reload(loop)

    @asynccontextmanager
    async def _reload_lifespan(starlette_app: Any):
        loop_cell[0] = asyncio.get_running_loop()
        watcher = threading.Thread(target=_watch, daemon=True)
        watcher.start()

        async def _sweep() -> None:
            while True:
                await asyncio.sleep(config.sweep_interval)
                await sessions.sweep()

        sweep_task = asyncio.create_task(_sweep())
        try:
            yield
        finally:
            stop_event.set()
            loop_cell[0] = None
            sweep_task.cancel()
            await asyncio.gather(sweep_task, return_exceptions=True)
            await sessions.close_all()

    return Starlette(routes=routes, lifespan=_reload_lifespan)


def find_available_port(
    host: str = "127.0.0.1", start_port: int = 8000, max_attempts: int = 100
) -> int:
    """Find an available TCP port starting from ``start_port``."""
    for port in range(start_port, start_port + max_attempts):
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        for family, socktype, protocol, _, address in addresses:
            try:
                with socket.socket(family, socktype, protocol) as sock:
                    sock.bind(address)
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
    uvicorn.run(
        starlette_app,
        host=host,
        port=actual_port,
        reload=False,
        ws_max_size=app.web.max_message_bytes,
    )


__all__ = ["create_web_app", "find_available_port", "run_app"]
