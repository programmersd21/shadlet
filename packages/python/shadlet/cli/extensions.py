"""Extension project scaffolding and validation commands."""

from __future__ import annotations

import importlib
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from shadlet.extensions import ExtensionManifest
from shadlet.version import __version__

extension_app = typer.Typer(
    name="extension",
    help="create and validate React component extensions",
    no_args_is_help=True,
)
console = Console()
_EXTENSION_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")


def _extension_files(name: str, module: str) -> dict[str, str]:
    project_name = f"shadlet-{name}"
    component_type = f"{name}:Notice"
    js_global = module.title().replace("_", "")
    next_minor = ".".join(__version__.split(".")[:2])
    major, minor = (int(value) for value in next_minor.split("."))
    upper_bound = f"{major}.{minor + 1}.0"

    return {
        "pyproject.toml": f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["shadlet>={__version__},<{upper_bound}"]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "build>=1.0.0"]

[project.entry-points."shadlet.extensions"]
{name} = "{module}:extension"

[tool.hatch.build.targets.wheel]
packages = ["src/{module}"]

[tool.hatch.build.targets.wheel.force-include]
"src/{module}/assets" = "{module}/assets"

[tool.pytest.ini_options]
pythonpath = ["src"]
''',
        f"src/{module}/__init__.py": f'''from importlib.resources import files

import shadlet as ui


class Notice(ui.Component):
    type = "{component_type}"

    def __init__(self, message: str, *, on_dismiss=None) -> None:
        super().__init__(message=message)
        self.bind("dismiss", on_dismiss)


def extension() -> ui.ExtensionManifest:
    return ui.ExtensionManifest(
        name="{name}",
        version="0.1.0",
        assets=files(__package__) / "assets",
        stylesheet="styles.css",
    )
''',
        "src/index.ts": f'''import React from "react";
import "./styles.css";

type AdapterProps = {{
  props: Record<string, unknown>;
  children?: React.ReactNode;
  events: Record<string, string>;
  dispatch: (event: string, payload: Record<string, unknown>) => void;
}};

declare global {{
  interface Window {{
    shadlet: {{
      loadExtension(extension: {{
        name: string;
        version: string;
        components: Record<string, React.ComponentType<AdapterProps>>;
      }}): void;
    }};
  }}
}}

function Notice({{ props, events, dispatch }}: AdapterProps) {{
  return React.createElement(
    "aside",
    {{ className: "{name}-notice" }},
    React.createElement("span", null, String(props.message ?? "")),
    events.dismiss
      ? React.createElement(
          "button",
          {{
            type: "button",
            "aria-label": "dismiss notice",
            onClick: () => dispatch("dismiss", {{}}),
          }},
          "dismiss",
        )
      : null,
  );
}}

window.shadlet.loadExtension({{
  name: "{name}",
  version: "0.1.0",
  components: {{ Notice }},
}});
''',
        "src/styles.css": f""".{name}-notice {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid currentColor;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
}}
""",
        "vite.config.ts": f'''import {{ defineConfig }} from "vite";

export default defineConfig({{
  build: {{
    outDir: "src/{module}/assets",
    emptyOutDir: true,
    lib: {{
      entry: "src/index.ts",
      formats: ["iife"],
      name: "{js_global}",
      fileName: () => "index.js",
    }},
    rollupOptions: {{
      external: ["react"],
      output: {{
        globals: {{ react: "React" }},
        assetFileNames: "styles.css",
      }},
    }},
  }},
}});
''',
        "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "skipLibCheck": true,
    "types": ["vite/client"]
  },
  "include": ["src/index.ts"]
}
""",
        "package.json": f'''{{
  "name": "{project_name}-browser",
  "private": true,
  "type": "module",
  "scripts": {{
    "build": "tsc --noEmit && vite build",
    "typecheck": "tsc --noEmit"
  }},
  "devDependencies": {{
    "@types/react": "^19.0.0",
    "react": "^19.0.0",
    "typescript": "^5.9.0",
    "vite": "^7.0.0"
  }}
}}
''',
        "README.md": f"""# {project_name}

a python package that adds a namespaced React component to shadlet.

## build and test

```bash
npm install
npm run build
uv pip install -e ".[dev]"
python -m pytest
shadlet extension check
```

the build writes `index.js` and `styles.css` into the Python package. build
these assets before creating or installing the wheel.

## install in an application

```bash
uv pip install .
```

the package registers its manifest through the `shadlet.extensions` entry
point. the application only needs Python; Node.js is required here by extension
authors to build the bundled browser files.

## package

```bash
python -m build
```

the wheel includes the generated browser assets. verify it with
`shadlet extension check` before distributing it.
""",
        "tests/test_extension.py": f'''from {module} import extension


def test_extension_manifest():
    manifest = extension()
    assert manifest.name == "{name}"
    assert manifest.version == "0.1.0"
    assert manifest.stylesheet_url is not None
    assert manifest.read_asset("index.js")
    assert manifest.read_asset("styles.css")
''',
    }


@extension_app.command("create")
def create(
    name: str = typer.Argument(..., help="lowercase extension namespace"),
    target: Path | None = typer.Option(None, "--target", help="target directory"),  # noqa: B008
) -> None:
    """scaffold a Python package and React bundle for an extension."""
    if not _EXTENSION_NAME.fullmatch(name):
        console.print(
            "[red]error:[/red] extension name must start with a lowercase letter "
            "and contain only lowercase letters, digits, hyphens, or underscores"
        )
        raise typer.Exit(code=1)

    destination = target or (Path.cwd() / name)
    if destination.exists():
        console.print(f"[red]error:[/red] destination already exists: {destination}")
        raise typer.Exit(code=1)

    module = name.replace("-", "_")
    created = False
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir()
        created = True
        for relative_path, content in _extension_files(name, module).items():
            path = destination / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    except OSError as error:
        if created and destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        console.print(f"[red]error:[/red] failed to scaffold extension: {error}")
        raise typer.Exit(code=1) from error

    console.print(f"[green]created[/green] extension project at {destination}")
    console.print(
        "  install browser build dependencies with [cyan]npm install[/cyan], "
        "then run [cyan]npm run build[/cyan]"
    )


@extension_app.command("check")
def check(
    path: Path = typer.Argument(Path("."), help="extension project directory"),  # noqa: B008
) -> None:
    """validate package metadata, entry point, manifest, and built assets."""
    root = path.resolve()
    project_file = root / "pyproject.toml"
    try:
        project_data: dict[str, Any] = tomllib.loads(
            project_file.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        console.print(f"[red]error:[/red] cannot read {project_file}: {error}")
        raise typer.Exit(code=1) from error

    project = project_data.get("project")
    declared_entry_points = (
        project.get("entry-points") if isinstance(project, dict) else None
    )
    entry_points = (
        declared_entry_points.get("shadlet.extensions")
        if isinstance(declared_entry_points, dict)
        else None
    )
    if not isinstance(project, dict) or not isinstance(project.get("name"), str):
        console.print("[red]error:[/red] pyproject.toml needs [project].name")
        raise typer.Exit(code=1)
    if not isinstance(entry_points, dict) or len(entry_points) != 1:
        console.print(
            "[red]error:[/red] define exactly one entry in "
            '[project.entry-points."shadlet.extensions"]'
        )
        raise typer.Exit(code=1)
    extension_name, target = next(iter(entry_points.items()))
    if not _EXTENSION_NAME.fullmatch(extension_name):
        console.print("[red]error:[/red] entry-point name is not a valid namespace")
        raise typer.Exit(code=1)
    if not isinstance(target, str) or target.count(":") != 1:
        console.print("[red]error:[/red] entry point must use module:attribute syntax")
        raise typer.Exit(code=1)
    module_name, attribute = target.split(":")
    if not module_name or not attribute:
        console.print("[red]error:[/red] entry point must use module:attribute syntax")
        raise typer.Exit(code=1)

    source_root = root / "src"
    module_path = source_root.joinpath(*module_name.split("."))
    if not (
        module_path.with_suffix(".py").is_file()
        or (module_path / "__init__.py").is_file()
    ):
        console.print(
            f"[red]error:[/red] entry-point module was not found under {source_root}"
        )
        raise typer.Exit(code=1)

    sys.path.insert(0, str(source_root))
    try:
        importlib.invalidate_caches()
        module = importlib.import_module(module_name)
        value: Any = module
        for part in attribute.split("."):
            value = getattr(value, part)
        manifest = value() if callable(value) else value
    except (ImportError, AttributeError, OSError, TypeError, ValueError) as error:
        console.print(f"[red]error:[/red] extension entry point failed: {error}")
        raise typer.Exit(code=1) from error
    finally:
        sys.path.remove(str(source_root))
        sys.modules.pop(module_name, None)

    if not isinstance(manifest, ExtensionManifest):
        console.print("[red]error:[/red] entry point must return an ExtensionManifest")
        raise typer.Exit(code=1)
    if manifest.name != extension_name:
        console.print("[red]error:[/red] manifest name must match the entry-point name")
        raise typer.Exit(code=1)
    if project.get("version") != manifest.version:
        console.print("[red]error:[/red] project and manifest versions must match")
        raise typer.Exit(code=1)
    module_directory = module_name.replace(".", "/")
    hatch = (
        project_data.get("tool", {}).get("hatch", {})
        if isinstance(project_data.get("tool"), dict)
        else {}
    )
    build = hatch.get("build", {}) if isinstance(hatch, dict) else {}
    targets = build.get("targets", {}) if isinstance(build, dict) else {}
    wheel = targets.get("wheel", {}) if isinstance(targets, dict) else {}
    force_include = wheel.get("force-include") if isinstance(wheel, dict) else None
    if (
        not isinstance(force_include, dict)
        or force_include.get(f"src/{module_directory}/assets")
        != f"{module_directory}/assets"
    ):
        console.print(
            "[red]error:[/red] configure wheel force-include for the package assets"
        )
        raise typer.Exit(code=1)

    console.print(
        f"[green]ok[/green] {project['name']} exposes "
        f"{manifest.name} {manifest.version}; manifest and wheel asset "
        "configuration are valid"
    )


__all__ = ["extension_app"]
