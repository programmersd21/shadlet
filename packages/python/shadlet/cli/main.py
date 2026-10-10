"""shadlet command line interface."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="shadlet",
    help="python-first web applications",
    no_args_is_help=True,
)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
    except Exception:  # noqa: BLE001, S110
        pass
console = Console()

TEMPLATES = {
    "minimal": "templates/minimal",
    "dashboard": "templates/dashboard",
    "landing-page": "templates/landing-page",
}


def _project_root() -> Path:
    return Path.cwd()


def _run(command: list[str], cwd: Path | None = None) -> int:
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, check=False)
    return result.returncode


@app.command()
def create(
    name: str = typer.Argument(..., help="project name"),
    template: str = typer.Option(
        "minimal", "--template", "-t", help="built-in or owner/repo template"
    ),
    target: Path | None = typer.Option(None, "--target", help="target directory"),  # noqa: B008
) -> None:
    """Create a new shadlet project."""
    destination = target or (Path.cwd() / name)
    if destination.exists():
        console.print(f"[red]error:[/red] destination already exists: {destination}")
        raise typer.Exit(code=1)
    destination.mkdir(parents=True)
    (destination / "assets").mkdir(exist_ok=True)
    from shadlet.templates.github import TemplateError, fetch_template

    if template in TEMPLATES:
        template_dir = Path(__file__).resolve().parents[4] / TEMPLATES[template]
        if not template_dir.exists():
            console.print(f"[red]error:[/red] template files missing: {template_dir}")
            raise typer.Exit(code=1)
        for item in template_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, destination / item.name)
            else:
                shutil.copy2(item, destination / item.name)
        console.print(f"[green]created[/green] {destination}")
        return

    try:
        manifest = fetch_template(template, destination)
        console.print(f"[green]created[/green] {destination} from {manifest.name}")
    except TemplateError as error:
        shutil.rmtree(destination, ignore_errors=True)
        console.print(f"[red]error:[/red] {error}")
        raise typer.Exit(code=1)


@app.command()
def dev(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="do not open the browser"
    ),
) -> None:
    """run the development server with auto-reload."""
    console.print("  shadlet  ·  development\n")
    if not Path("main.py").exists():
        console.print("[red]error:[/red] main.py not found")
        raise typer.Exit(code=1)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd()) + os.pathsep + env.get("PYTHONPATH", "")
    env["SHADLET_RELOAD"] = "1"
    from shadlet.web.server import find_available_port

    actual_port = find_available_port(host, port)
    if actual_port != port:
        console.print(
            f"  [yellow]![/yellow] port {port} in use, automatically switched to [cyan]{actual_port}[/cyan]"
        )
    port = actual_port
    env["SHADLET_PORT"] = str(actual_port)

    def start_server() -> subprocess.Popen:
        console.print("  · python server     starting")
        return subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(Path.cwd()),
            env=env,
        )

    def open_browser() -> None:
        if no_browser:
            return
        time.sleep(2)
        url = f"http://{host}:{port}"
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001, S110
            pass
        console.print(f"  local    {url}")

    import threading

    threading.Thread(target=open_browser, daemon=True).start()

    server = start_server()

    try:
        server.wait()
    except KeyboardInterrupt:
        console.print("\n  shutting down")
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()

    raise typer.Exit(code=0)


@app.command()
def run() -> None:
    """Run the application."""
    if not Path("main.py").exists():
        console.print("[red]error:[/red] main.py not found")
        raise typer.Exit(code=1)
    raise typer.Exit(code=_run([sys.executable, "main.py"]))


@app.command()
def doctor() -> None:
    """Check the local environment."""
    console.print("shadlet  ·  doctor\n")
    console.print(f"· python: {sys.version.split()[0]}")
    import shadlet as _sh

    renderer_candidates = [
        Path("packages/renderer") / "dist" / "index.html",
        Path(_sh.__file__).resolve().parent / "web" / "static" / "index.html",
    ]
    renderer_ok = any(c.exists() for c in renderer_candidates)
    if renderer_ok:
        console.print("· renderer: production bundle ready")
    else:
        console.print("[yellow]! renderer: bundle not yet built[/yellow]")

    console.print("\n· core framework ready")


@app.command()
def info() -> None:
    """Show framework information."""
    table = Table(title="shadlet")
    table.add_column("key")
    table.add_column("value")
    table.add_row("version", "0.1.0")
    table.add_row("python", sys.version.split()[0])
    table.add_row("renderer", "packages/renderer")
    console.print(table)


@app.command()
def clean() -> None:
    """Remove build artifacts."""
    for path in ("dist", "build", ".cache", "packages/renderer/dist"):
        target = Path(path)
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
    console.print("· cleaned")


if __name__ == "__main__":
    app()
