"""shadlet command line interface."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from shadlet.cli.extensions import extension_app

app = typer.Typer(
    name="shadlet",
    help="python-first web applications",
    no_args_is_help=True,
)
app.add_typer(extension_app, name="extension")
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
    except Exception:  # noqa: BLE001, S110
        pass
console = Console()

TEMPLATES = frozenset(
    {"minimal", "dashboard", "landing-page", "settings", "auth", "crud"}
)


def _project_root() -> Path:
    return Path.cwd()


def _builtin_template_directory(name: str) -> Path:
    package_templates = Path(__file__).resolve().parents[1] / "templates" / "builtin"
    repository_templates = Path(__file__).resolve().parents[4] / "templates"
    for candidate in (
        package_templates / name,
        repository_templates / name,
    ):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"built-in template files missing: {name}")


def _run(command: list[str], cwd: Path | None = None) -> int:
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, check=False)
    return result.returncode


@app.command()
def create(
    name: str | None = typer.Argument(None, help="project name"),
    template: str = typer.Option(
        "minimal", "--template", "-t", help="built-in or owner/repo template"
    ),
    target: Path | None = typer.Option(None, "--target", help="target directory"),  # noqa: B008
    variable: list[str] | None = typer.Option(  # noqa: B008
        None, "--var", help="override a declared template variable (KEY=VALUE)"
    ),
    token: str | None = typer.Option(
        None,
        "--token",
        help="GitHub token; prefer the GITHUB_TOKEN environment variable",
    ),
) -> None:
    """Create a new shadlet project."""
    from shadlet.templates.github import (
        MANIFEST_NAME,
        TemplateError,
        TemplateManifest,
        fetch_template,
        parse_template_ref,
        validate_template_directory,
    )
    from shadlet.version import __version__

    if name is None:
        if template in TEMPLATES:
            name = template
        else:
            try:
                template_ref = parse_template_ref(template)
            except TemplateError as error:
                console.print(f"[red]error:[/red] {error}")
                raise typer.Exit(code=1) from error
            name = (
                template_ref.subdir.rsplit("/", 1)[-1]
                if template_ref.subdir
                else template_ref.repo
            )
    if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", name):
        console.print("[red]error:[/red] project name contains unsupported characters")
        raise typer.Exit(code=1)
    destination = target or (Path.cwd() / name)
    if destination.exists():
        console.print(f"[red]error:[/red] destination already exists: {destination}")
        raise typer.Exit(code=1)
    variables: dict[str, str] = {}
    try:
        for item in variable or []:
            key, separator, value = item.partition("=")
            if not separator or not key:
                raise TemplateError(f"invalid --var {item!r}; expected KEY=VALUE")
            if key in variables:
                raise TemplateError(
                    f"template variable {key!r} was provided more than once"
                )
            variables[key] = value
    except TemplateError as error:
        console.print(f"[red]error:[/red] {error}")
        raise typer.Exit(code=1) from error
    created_destination = False

    def remove_partial_destination() -> None:
        if (
            created_destination
            and destination.is_dir()
            and not destination.is_symlink()
        ):
            shutil.rmtree(destination)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
        created_destination = True
        if template in TEMPLATES:
            template_dir = _builtin_template_directory(template)
            validation_errors = validate_template_directory(template_dir)
            if validation_errors:
                raise TemplateError(
                    f"invalid built-in template {template!r}: "
                    + "; ".join(validation_errors)
                )
            manifest = TemplateManifest.from_toml(
                (template_dir / MANIFEST_NAME).read_text(encoding="utf-8")
            )
            for source_item in template_dir.iterdir():
                target_path = destination / source_item.name
                if source_item.is_dir():
                    shutil.copytree(source_item, target_path)
                else:
                    shutil.copy2(source_item, target_path)
        else:
            manifest = fetch_template(template, destination, token=token)
        manifest.ensure_compatible(__version__)
        render_variables = dict(variables)
        if "project_name" in manifest.variables and "project_name" not in variables:
            render_variables["project_name"] = name
        manifest.render_variables(destination, overrides=render_variables)
        description = f" - {manifest.description}" if manifest.description else ""
        author = f" by {manifest.author}" if manifest.author else ""
        console.print(
            f"[green]created[/green] {destination} from "
            f"{manifest.name} {manifest.version}{author}{description}"
        )
    except TemplateError as error:
        try:
            remove_partial_destination()
        except OSError as cleanup_error:
            console.print(
                f"[red]error:[/red] could not remove partial project: {cleanup_error}"
            )
        console.print(f"[red]error:[/red] {error}")
        raise typer.Exit(code=1) from error
    except (OSError, UnicodeError) as error:
        try:
            remove_partial_destination()
        except OSError as cleanup_error:
            console.print(
                f"[red]error:[/red] could not remove partial project: {cleanup_error}"
            )
        console.print(f"[red]error:[/red] failed to create project: {error}")
        raise typer.Exit(code=1) from error


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
    import shadlet as _sh

    renderer_candidates = [
        Path("packages/renderer") / "dist" / "index.html",
        Path(_sh.__file__).resolve().parent / "web" / "static" / "index.html",
    ]
    renderer_status = (
        "ready" if any(c.exists() for c in renderer_candidates) else "not built"
    )
    banner = Text("shadlet", style="bold cyan")
    body = Table.grid(padding=(0, 2))
    body.add_row("version", _sh.__version__)
    body.add_row("python", sys.version.split()[0])
    body.add_row("renderer", renderer_status)
    body.add_row("runtime", "web (starlette + uvicorn)")
    panel = Panel(
        body,
        title=banner,
        subtitle="python-first web framework",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


if __name__ == "__main__":
    app()
