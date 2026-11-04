"""Safe GitHub project template fetching and validation."""

from __future__ import annotations

import io
import json
import os
import re
import tarfile
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 100 * 1024 * 1024
MANIFEST_NAME = "shadlet-template.toml"
_VERSION_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)
_VARIABLE_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


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
            ref = urllib.parse.quote(self.ref, safe="/")
            return f"https://github.com/{self.owner}/{self.repo}/archive/{ref}.tar.gz"
        return f"https://github.com/{self.owner}/{self.repo}/archive/HEAD.tar.gz"


@dataclass(frozen=True, slots=True)
class TemplateManifest:
    name: str
    description: str = ""
    version: str = "0.4.0"
    author: str = ""
    min_shadlet: str = "0.4.0"
    variables: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.variables, dict):
            raise TemplateError("variables must be a string-to-string mapping")
        object.__setattr__(self, "variables", dict(self.variables))
        if not isinstance(self.name, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+", self.name
        ):
            raise TemplateError(f"invalid template name {self.name!r}")
        for field_name in ("description", "version", "author", "min_shadlet"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str):
                raise TemplateError(f"template.{field_name} must be a string")
        _version_key(self.version)
        _version_key(self.min_shadlet)
        if not isinstance(self.variables, dict) or not all(
            isinstance(key, str)
            and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key)
            and isinstance(value, str)
            for key, value in self.variables.items()
        ):
            raise TemplateError("variables must be a string-to-string mapping")

    @classmethod
    def from_toml(cls, text: str) -> TemplateManifest:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            raise TemplateError(f"invalid TOML: {error}") from error
        if not isinstance(data, dict):
            raise TemplateError("manifest must contain a TOML table")
        unknown_sections = set(data) - {"template", "project", "variables"}
        if unknown_sections:
            raise TemplateError(
                f"unsupported manifest section(s): {', '.join(sorted(unknown_sections))}"
            )
        template = data.get("template", {})
        project = data.get("project", {})
        variables = data.get("variables", {})
        if not isinstance(template, dict):
            raise TemplateError("template must be a table")
        if not isinstance(project, dict):
            raise TemplateError("project must be a table")
        if not isinstance(variables, dict):
            raise TemplateError("variables must be a table")
        allowed_template_keys = {
            "name",
            "description",
            "version",
            "author",
            "min_shadlet",
        }
        unknown_template_keys = set(template) - allowed_template_keys
        if unknown_template_keys:
            raise TemplateError(
                "unsupported template field(s): "
                + ", ".join(sorted(unknown_template_keys))
            )
        if set(project) - {"name"}:
            raise TemplateError("project table only supports the name field")
        template_name = template.get("name")
        project_name = project.get("name")
        if template_name is not None and project_name is not None:
            raise TemplateError("use either template.name or project.name, not both")
        name = template_name if template_name is not None else project_name
        if not isinstance(name, str) or not name:
            raise TemplateError("manifest requires template.name")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise TemplateError(f"invalid template name {name!r}")
        for field_name in ("description", "version", "author", "min_shadlet"):
            field_value = template.get(field_name)
            if field_value is not None and not isinstance(field_value, str):
                raise TemplateError(f"template.{field_name} must be a string")
        version = template.get("version", "0.4.0")
        min_shadlet = template.get("min_shadlet", "0.4.0")
        _version_key(version)
        _version_key(min_shadlet)
        if not all(
            isinstance(key, str)
            and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key)
            and isinstance(value, str)
            for key, value in variables.items()
        ):
            raise TemplateError("variables must be a string-to-string mapping")
        return cls(
            name=name,
            description=template.get("description", ""),
            version=version,
            author=template.get("author", ""),
            min_shadlet=min_shadlet,
            variables=dict(variables),
        )

    def ensure_compatible(self, shadlet_version: str) -> None:
        if _version_is_less(
            _version_key(shadlet_version), _version_key(self.min_shadlet)
        ):
            raise TemplateError(
                f"template {self.name!r} requires shadlet>={self.min_shadlet}; "
                f"installed version is {shadlet_version}"
            )

    def render_variables(
        self,
        directory: Path,
        *,
        overrides: dict[str, str] | None = None,
    ) -> None:
        values = dict(self.variables)
        for key, value in (overrides or {}).items():
            if key not in values:
                raise TemplateError(f"template does not declare variable {key!r}")
            if not isinstance(value, str):
                raise TemplateError(f"template variable {key!r} must be a string")
            values[key] = value
        if not values:
            return

        referenced: set[str] = set()
        updates: list[tuple[Path, str]] = []
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise TemplateError(f"symlink not allowed in template: {path}")
            if not path.is_file():
                continue
            try:
                content = path.read_bytes()
                if b"\x00" in content:
                    continue
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                continue
            referenced.update(
                match.group(1) for match in _VARIABLE_PATTERN.finditer(text)
            )
            rendered = _VARIABLE_PATTERN.sub(
                lambda match: values.get(match.group(1), match.group(0)), text
            )
            if rendered != text:
                updates.append((path, rendered))
        unused = set(values) - referenced
        if unused:
            raise TemplateError(
                "declared template variable(s) are not used in text files: "
                + ", ".join(sorted(unused))
            )
        for path, rendered in updates:
            path.write_text(rendered, encoding="utf-8", newline="")


def _version_key(
    version: str,
) -> tuple[tuple[int, int, int], tuple[tuple[int, int | str], ...] | None]:
    if not isinstance(version, str):
        raise TemplateError(f"invalid semantic version {version!r}")
    match = _VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise TemplateError(f"invalid semantic version {version!r}")
    major, minor, patch, prerelease, build = match.groups()
    for suffix in (prerelease, build):
        if suffix is not None and any(
            not re.fullmatch(r"[0-9A-Za-z-]+", part) for part in suffix.split(".")
        ):
            raise TemplateError(f"invalid semantic version {version!r}")
    if prerelease is None:
        prerelease_key = None
    else:
        parts: list[tuple[int, int | str]] = []
        for part in prerelease.split("."):
            if part.isdigit():
                if len(part) > 1 and part.startswith("0"):
                    raise TemplateError(f"invalid semantic version {version!r}")
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        prerelease_key = tuple(parts)
    return (int(major), int(minor), int(patch)), prerelease_key


def _version_is_less(
    left: tuple[tuple[int, int, int], tuple[tuple[int, int | str], ...] | None],
    right: tuple[tuple[int, int, int], tuple[tuple[int, int | str], ...] | None],
) -> bool:
    if left[0] != right[0]:
        return left[0] < right[0]
    left_pre, right_pre = left[1], right[1]
    if left_pre is None:
        return False
    if right_pre is None:
        return True
    for left_part, right_part in zip(left_pre, right_pre):
        if left_part != right_part:
            return left_part < right_part
    return len(left_pre) < len(right_pre)


def parse_template_ref(spec: str) -> TemplateRef:
    if not isinstance(spec, str) or not spec.strip():
        raise TemplateError("template spec must be a non-empty string")
    spec = spec.strip()
    if spec.startswith(("https://", "http://")):
        try:
            parsed = urllib.parse.urlparse(spec)
            port = parsed.port
        except ValueError as error:
            raise TemplateError(f"invalid github url: {spec}") from error
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or port is not None
            or parsed.query
        ):
            raise TemplateError("template URLs must use https://github.com/")
        parts = [
            urllib.parse.unquote(part)
            for part in parsed.path.strip("/").split("/")
            if part
        ]
        if len(parts) < 2:
            raise TemplateError(f"invalid github url: {spec}")
        owner, repo = parts[0], parts[1]
        ref = None
        subdir = None
        if len(parts) != 2:
            if len(parts) >= 4 and parts[2] == "tree":
                ref = parts[3]
                subdir = "/".join(parts[4:]) if len(parts) > 4 else None
            else:
                raise TemplateError(f"unsupported github url path: {spec}")
        if parsed.fragment:
            ref = urllib.parse.unquote(parsed.fragment)
        return _validated_template_ref(owner, repo, ref, subdir)

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

    return _validated_template_ref(owner, repo, ref, subdir)


def _validated_template_ref(
    owner: str,
    repo: str,
    ref: str | None,
    subdir: str | None,
) -> TemplateRef:
    if (
        not re.fullmatch(r"[A-Za-z0-9_.-]+", owner)
        or owner in {".", ".."}
        or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo)
        or repo in {".", ".."}
    ):
        raise TemplateError(f"invalid owner or repository: {owner!r}/{repo!r}")
    if ref is not None and (
        not re.fullmatch(r"[A-Za-z0-9_.\-/]+", ref)
        or ref.startswith("/")
        or ref.endswith("/")
        or "//" in ref
        or ".." in ref.split("/")
    ):
        raise TemplateError(f"invalid git ref {ref!r}")
    if subdir is not None:
        subdir = subdir.strip("/")
        if (
            not subdir
            or "\\" in subdir
            or "\x00" in subdir
            or any(part in {"", ".", ".."} for part in subdir.split("/"))
        ):
            raise TemplateError("subdirectory must contain only safe relative paths")
    return TemplateRef(owner=owner, repo=repo, ref=ref, subdir=subdir)


def _safe_member_path(member_name: str) -> Path | None:
    name = member_name.replace("\\", "/")
    windows_path = PureWindowsPath(member_name)
    if (
        not name
        or "\x00" in name
        or name.startswith("/")
        or windows_path.drive
        or ".." in name.split("/")
        or any(":" in part for part in name.split("/"))
        or any(part in {"", "."} for part in name.rstrip("/").split("/"))
    ):
        return None
    return Path(*PurePosixPath(name).parts)


def _extract_tarball(data: bytes, destination: Path, subdir: str | None) -> Path:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise TemplateError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
    extracted_bytes = 0
    extracted_files = 0
    root_dir: str | None = None
    member_paths: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            if member.issym() or member.islnk() or member.isdev():
                raise TemplateError(f"unsafe archive member: {member.name}")
            safe = _safe_member_path(member.name)
            if safe is None:
                raise TemplateError(f"unsafe archive path: {member.name}")
            normalized = safe.as_posix()
            if normalized in member_paths:
                raise TemplateError(f"duplicate archive path: {member.name}")
            member_paths.add(normalized)
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
            safe_relative = _safe_member_path(relative)
            if safe_relative is None:
                raise TemplateError(f"unsafe archive path: {member.name}")
            target = destination / safe_relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            extracted_bytes += member.size
            if extracted_bytes > MAX_EXTRACTED_BYTES:
                raise TemplateError("extracted content exceeds size limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise TemplateError(f"could not read archive member: {member.name}")
            content = source.read(member.size + 1)
            if len(content) != member.size:
                raise TemplateError(f"archive member size mismatch: {member.name}")
            target.write_bytes(content)
            if member.mode:
                target.chmod(member.mode & 0o777)
            extracted_files += 1
    if extracted_files == 0:
        raise TemplateError("template archive contains no files for the selected path")
    return destination


def fetch_template(
    spec: str, destination: Path, *, token: str | None = None
) -> TemplateManifest:
    ref = parse_template_ref(spec)
    if destination.is_symlink():
        raise TemplateError("destination must not be a symlink")
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

    try:
        _extract_tarball(data, destination, ref.subdir)
    except (tarfile.TarError, OSError, EOFError) as error:
        raise TemplateError(f"invalid template archive: {error}") from error

    manifest_path = destination / MANIFEST_NAME
    if not manifest_path.exists():
        manifest = TemplateManifest(name=f"{ref.owner}-{ref.repo}")
        manifest_path.write_text(_render_default_manifest(manifest))
        return manifest
    try:
        manifest = TemplateManifest.from_toml(manifest_path.read_text(encoding="utf-8"))
    except (TemplateError, OSError, UnicodeError) as error:
        raise TemplateError(f"invalid template manifest: {error}") from error
    return manifest


def _render_default_manifest(manifest: TemplateManifest) -> str:
    return (
        "[template]\n"
        f"name = {json.dumps(manifest.name)}\n"
        f"description = {json.dumps(manifest.description)}\n"
        f"version = {json.dumps(manifest.version)}\n"
        f"author = {json.dumps(manifest.author)}\n"
        f"min_shadlet = {json.dumps(manifest.min_shadlet)}\n"
    )


def validate_template_directory(path: Path) -> list[str]:
    errors: list[str] = []
    if path.is_symlink():
        return ["template directory must not be a symlink"]
    if not path.exists() or not path.is_dir():
        return ["template directory does not exist"]
    for item in path.rglob("*"):
        if item.is_symlink():
            errors.append(f"symlink not allowed: {item}")
    if errors:
        return errors
    manifest_path = path / MANIFEST_NAME
    if not manifest_path.exists():
        errors.append(f"missing {MANIFEST_NAME}")
        return errors
    try:
        TemplateManifest.from_toml(manifest_path.read_text(encoding="utf-8"))
    except (TemplateError, OSError, UnicodeError) as error:
        errors.append(str(error))
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
