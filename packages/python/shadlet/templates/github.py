"""Safe GitHub project template fetching and validation."""

from __future__ import annotations

import io
import os
import re
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 100 * 1024 * 1024
MANIFEST_NAME = "shadlet-template.toml"


class TemplateError(ValueError):
    """Raised when a template cannot be fetched or validated."""


@dataclass(frozen=True, slots=True)
class TemplateRef:
    owner: str
    repo: str
    ref: str | None = None
    subdir: str | None = None

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"

    @property
    def tarball_url(self) -> str:
        if self.ref:
            return (
                f"https://github.com/{self.owner}/{self.repo}/archive/{self.ref}.tar.gz"
            )
        return f"https://github.com/{self.owner}/{self.repo}/archive/HEAD.tar.gz"


@dataclass(frozen=True, slots=True)
class TemplateManifest:
    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = ""
    min_shadlet: str = "0.1.0"
    python_dependencies: tuple[str, ...] = ()
    npm_dependencies: tuple[str, ...] = ()
    variables: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_toml(cls, text: str) -> TemplateManifest:
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(text)
        template = data.get("template", {})
        project = data.get("project", {})
        deps = data.get("dependencies", {})
        variables = data.get("variables", {})
        name = template.get("name") or project.get("name")
        if not isinstance(name, str) or not name:
            raise TemplateError("manifest requires template.name")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise TemplateError(f"invalid template name {name!r}")
        python_deps = deps.get("python", [])
        npm_deps = deps.get("npm", [])
        if not isinstance(python_deps, list) or not all(
            isinstance(x, str) for x in python_deps
        ):
            raise TemplateError("dependencies.python must be a list of strings")
        if not isinstance(npm_deps, list) or not all(
            isinstance(x, str) for x in npm_deps
        ):
            raise TemplateError("dependencies.npm must be a list of strings")
        if not isinstance(variables, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in variables.items()
        ):
            raise TemplateError("variables must be a string-to-string mapping")
        return cls(
            name=name,
            description=str(template.get("description", "")),
            version=str(template.get("version", "0.1.0")),
            author=str(template.get("author", "")),
            min_shadlet=str(template.get("min_shadlet", "0.1.0")),
            python_dependencies=tuple(python_deps),
            npm_dependencies=tuple(npm_deps),
            variables=dict(variables),
        )


def parse_template_ref(spec: str) -> TemplateRef:
    if not isinstance(spec, str) or not spec.strip():
        raise TemplateError("template spec must be a non-empty string")
    spec = spec.strip()
    if spec.startswith(("https://github.com/", "http://github.com/")):
        parsed = urllib.parse.urlparse(spec)
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise TemplateError(f"invalid github url: {spec}")
        owner, repo = parts[0], parts[1]
        ref = None
        subdir = None
        if len(parts) >= 4 and parts[2] == "tree":
            ref = parts[3]
            subdir = "/".join(parts[4:]) if len(parts) > 4 else None
        if "#" in spec:
            ref = spec.split("#", 1)[1] or ref
        return TemplateRef(owner=owner, repo=repo, ref=ref, subdir=subdir)

    if "#" in spec:
        spec, ref = spec.split("#", 1)
        ref = ref or None
    else:
        ref = None

    if "/" in spec:
        owner, rest = spec.split("/", 1)
        if "/" in rest:
            repo, subdir = rest.split("/", 1)
        else:
            repo, subdir = rest, None
    else:
        raise TemplateError(f"invalid template spec: {spec!r}; expected owner/repo")

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", repo
    ):
        raise TemplateError(f"invalid owner or repo in {spec!r}")
    if ref is not None and not re.fullmatch(r"[A-Za-z0-9_.\-/]+", ref):
        raise TemplateError(f"invalid git ref {ref!r}")
    if subdir is not None:
        subdir = subdir.strip("/")
        if ".." in subdir.split("/") or subdir.startswith("/"):
            raise TemplateError("subdirectory must not contain '..' or be absolute")
    return TemplateRef(owner=owner, repo=repo, ref=ref, subdir=subdir)


def _safe_member_path(member_name: str) -> Path | None:
    name = member_name.replace("\\", "/")
    if name.startswith("/") or ".." in name.split("/"):
        return None
    return Path(name)


def _extract_tarball(data: bytes, destination: Path, subdir: str | None) -> Path:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise TemplateError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
    extracted_bytes = 0
    root_dir: str | None = None
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            if member.issym() or member.islnk() or member.isdev():
                raise TemplateError(f"unsafe archive member: {member.name}")
            safe = _safe_member_path(member.name)
            if safe is None:
                raise TemplateError(f"unsafe archive path: {member.name}")
        top_levels = {m.name.split("/", 1)[0] for m in members if "/" in m.name}
        if len(top_levels) != 1:
            raise TemplateError("archive must contain a single top-level directory")
        root_dir = next(iter(top_levels))
        prefix = root_dir + "/"
        if subdir:
            base_prefix = prefix + subdir.strip("/") + "/"
        else:
            base_prefix = prefix
        for member in members:
            if not member.name.startswith(base_prefix):
                continue
            if not member.isfile() and not member.isdir():
                continue
            relative = member.name[len(base_prefix) :]
            if not relative:
                continue
            target = destination / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            extracted_bytes += member.size
            if extracted_bytes > MAX_EXTRACTED_BYTES:
                raise TemplateError("extracted content exceeds size limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                continue
            target.write_bytes(source.read())
    return destination


def fetch_template(
    spec: str, destination: Path, *, token: str | None = None
) -> TemplateManifest:
    ref = parse_template_ref(spec)
    if destination.exists() and any(destination.iterdir()):
        raise TemplateError(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "shadlet"}
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

    url = ref.tarball_url
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(MAX_ARCHIVE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise TemplateError(
            f"failed to download template: HTTP {error.code}"
        ) from error
    except urllib.error.URLError as error:
        raise TemplateError(f"failed to download template: {error.reason}") from error
    if len(data) > MAX_ARCHIVE_BYTES:
        raise TemplateError("template archive is too large")

    _extract_tarball(data, destination, ref.subdir)

    manifest_path = destination / MANIFEST_NAME
    if not manifest_path.exists():
        # allow templates without manifest but create a default
        manifest = TemplateManifest(name=f"{ref.owner}/{ref.repo}")
        manifest_path.write_text(_render_default_manifest(manifest))
        return manifest
    try:
        manifest = TemplateManifest.from_toml(manifest_path.read_text())
    except Exception as error:
        raise TemplateError(f"invalid template manifest: {error}") from error
    return manifest


def _render_default_manifest(manifest: TemplateManifest) -> str:
    return (
        "[template]\n"
        f'name = "{manifest.name}"\n'
        'description = ""\n'
        f'version = "{manifest.version}"\n'
        'author = ""\n'
        f'min_shadlet = "{manifest.min_shadlet}"\n'
    )


def validate_template_directory(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists() or not path.is_dir():
        return ["template directory does not exist"]
    manifest_path = path / MANIFEST_NAME
    if not manifest_path.exists():
        errors.append(f"missing {MANIFEST_NAME}")
        return errors
    try:
        TemplateManifest.from_toml(manifest_path.read_text())
    except TemplateError as error:
        errors.append(str(error))
    # path traversal / symlink check
    for item in path.rglob("*"):
        if item.is_symlink():
            errors.append(f"symlink not allowed: {item}")
    return errors


__all__ = [
    "MANIFEST_NAME",
    "MAX_ARCHIVE_BYTES",
    "TemplateError",
    "TemplateManifest",
    "TemplateRef",
    "fetch_template",
    "parse_template_ref",
    "validate_template_directory",
]
