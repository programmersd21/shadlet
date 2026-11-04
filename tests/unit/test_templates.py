import io
import tarfile

import pytest
from shadlet.cli.main import app as cli_app
from shadlet.templates.github import (
    TemplateError,
    TemplateManifest,
    _extract_tarball,
    _render_default_manifest,
    fetch_template,
    parse_template_ref,
    validate_template_directory,
)
from typer.testing import CliRunner


def test_parse_owner_repo():
    ref = parse_template_ref("owner/repo")
    assert ref.owner == "owner"
    assert ref.repo == "repo"
    assert ref.ref is None
    assert ref.subdir is None


def test_parse_branch_and_subdir():
    ref = parse_template_ref("owner/repo/subdir#v1")
    assert ref.owner == "owner"
    assert ref.repo == "repo"
    assert ref.subdir == "subdir"
    assert ref.ref == "v1"


def test_parse_full_url():
    ref = parse_template_ref(
        "https://github.com/acme/toolkit/tree/main/examples/dashboard"
    )
    assert ref.owner == "acme"
    assert ref.repo == "toolkit"
    assert ref.ref == "main"
    assert ref.subdir == "examples/dashboard"


def test_parse_rejects_traversal():
    with pytest.raises(TemplateError):
        parse_template_ref("owner/repo/../evil")


@pytest.mark.parametrize(
    "spec",
    [
        "http://github.com/acme/demo",
        "https://github.com.evil/acme/demo",
        "https://user@github.com/acme/demo",
        "https://github.com:invalid/acme/demo",
        "https://github.com/acme/demo/archive/main",
        "https://github.com/acme/demo/tree/main/../secret",
        "acme/demo/../secret",
    ],
)
def test_parse_rejects_unsafe_github_references(spec):
    with pytest.raises(TemplateError):
        parse_template_ref(spec)


def test_manifest_round_trip():
    text = """
[template]
name = "demo"
description = "sample project"
version = "1.0.0"
author = "me"
min_shadlet = "0.3.0"

[variables]
title = "Demo"
"""
    manifest = TemplateManifest.from_toml(text)
    assert manifest.name == "demo"
    assert manifest.description == "sample project"
    assert manifest.version == "1.0.0"
    assert manifest.author == "me"
    assert manifest.min_shadlet == "0.3.0"
    assert manifest.variables == {"title": "Demo"}


def test_manifest_rejects_bad_name():
    with pytest.raises(TemplateError):
        TemplateManifest.from_toml('[template]\nname = "bad/name"\n')


def test_manifest_accepts_project_name_compatibility_fallback():
    manifest = TemplateManifest.from_toml('[project]\nname = "demo"\n')
    assert manifest.name == "demo"


def test_manifest_rejects_ambiguous_template_and_project_names():
    with pytest.raises(TemplateError, match="use either"):
        TemplateManifest.from_toml(
            '[template]\nname = "demo"\n[project]\nname = "other"\n'
        )


def test_manifest_rejects_unsupported_dependency_section():
    with pytest.raises(TemplateError, match="unsupported manifest section"):
        TemplateManifest.from_toml(
            '[template]\nname = "demo"\n[dependencies]\npython = ["shadlet"]\n'
        )


@pytest.mark.parametrize(
    "text",
    [
        '[template]\nname = "demo"\nversion = 1\n',
        '[template]\nname = "demo"\nmin_shadlet = "latest"\n',
        '[template]\nname = "demo"\nversion = "1.0.0-01"\n',
        '[template]\nname = "demo"\n[variables]\ntitle = 1\n',
        '[template]\nname = "demo"\n[variables]\n"bad-key" = "value"\n',
        '[template]\nname = "demo"\nunknown = "ignored?"\n',
    ],
)
def test_manifest_rejects_invalid_or_unknown_fields(text):
    with pytest.raises(TemplateError):
        TemplateManifest.from_toml(text)


@pytest.mark.parametrize(
    ("installed", "minimum", "compatible"),
    [
        ("0.3.0", "0.3.0", True),
        ("0.3.1", "0.3.0", True),
        ("0.2.9", "0.3.0", False),
        ("0.3.0", "0.3.1", False),
        ("0.3.0", "0.3.0-rc.1", True),
        ("0.3.0-rc.1", "0.3.0", False),
        ("0.3.0+build.2", "0.3.0+build.1", True),
        ("0.3.0", "0.3.0-rc.1+build.1", True),
    ],
)
def test_manifest_enforces_minimum_shadlet_version(installed, minimum, compatible):
    manifest = TemplateManifest.from_toml(
        f'[template]\nname = "demo"\nmin_shadlet = "{minimum}"\n'
    )
    if compatible:
        manifest.ensure_compatible(installed)
    else:
        with pytest.raises(TemplateError, match="requires shadlet"):
            manifest.ensure_compatible(installed)


def test_manifest_renders_declared_variables_and_preserves_binary_files(tmp_path):
    manifest = TemplateManifest.from_toml(
        '[template]\nname = "demo"\n[variables]\ntitle = "default"\n'
    )
    (tmp_path / "main.py").write_text('title = "{{ title }}"\n')
    (tmp_path / "image.bin").write_bytes(b"\x00{{ title }}")
    (tmp_path / "other.txt").write_text("{{ undeclared }}")

    manifest.render_variables(tmp_path, overrides={"title": "custom"})

    assert (tmp_path / "main.py").read_text() == 'title = "custom"\n'
    assert (tmp_path / "image.bin").read_bytes() == b"\x00{{ title }}"
    assert (tmp_path / "other.txt").read_text() == "{{ undeclared }}"


def test_manifest_rejects_overrides_for_undeclared_variables(tmp_path):
    manifest = TemplateManifest.from_toml('[template]\nname = "demo"\n')
    with pytest.raises(TemplateError, match="does not declare"):
        manifest.render_variables(tmp_path, overrides={"title": "demo"})


def test_manifest_rejects_unused_variables_without_partial_render(tmp_path):
    manifest = TemplateManifest.from_toml(
        '[template]\nname = "demo"\n[variables]\ntitle = "default"\nunused = "value"\n'
    )
    target = tmp_path / "main.py"
    target.write_text('title = "{{ title }}"\n')
    with pytest.raises(TemplateError, match="not used"):
        manifest.render_variables(tmp_path)
    assert target.read_text() == 'title = "{{ title }}"\n'


def _archive(entries: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in entries:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_extract_tarball_only_writes_selected_subdirectory(tmp_path):
    data = _archive(
        [
            ("repo/README.md", b"root"),
            ("repo/examples/demo/main.py", b"app"),
        ]
    )
    _extract_tarball(data, tmp_path, "examples/demo")
    assert (tmp_path / "main.py").read_bytes() == b"app"
    assert not (tmp_path / "README.md").exists()


def test_extract_tarball_rejects_duplicate_paths(tmp_path):
    with pytest.raises(TemplateError, match="duplicate archive path"):
        _extract_tarball(
            _archive([("repo/file.txt", b"first"), ("repo/file.txt", b"second")]),
            tmp_path,
            None,
        )


@pytest.mark.parametrize(
    "member_name",
    [
        "repo/../outside.txt",
        "repo/C:/outside.txt",
        "repo\\..\\outside.txt",
        "/outside.txt",
    ],
)
def test_extract_tarball_rejects_unsafe_paths(tmp_path, member_name):
    with pytest.raises(TemplateError, match="unsafe archive path"):
        _extract_tarball(_archive([(member_name, b"unsafe")]), tmp_path, None)


def test_fetch_template_uses_manifest_and_github_token(tmp_path, monkeypatch):
    manifest = (
        '[template]\nname = "remote-demo"\nversion = "1.2.0"\n'
        'min_shadlet = "0.3.0"\n\n[variables]\ntitle = "default"\n'
    )
    archive = _archive(
        [
            ("repo/shadlet-template.toml", manifest.encode()),
            ("repo/main.py", b'app = "{{ title }}"\n'),
        ]
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, _limit):
            return archive

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    from shadlet.templates import github

    monkeypatch.setattr(github.urllib.request, "urlopen", fake_urlopen)
    destination = tmp_path / "remote"
    loaded = fetch_template("owner/repo#v1.2.0", destination, token="test-token")
    loaded.ensure_compatible("0.3.0")
    loaded.render_variables(destination, overrides={"title": "rendered"})

    request = captured["request"]
    assert request.full_url.endswith("/owner/repo/archive/v1.2.0.tar.gz")
    assert request.get_header("Authorization") == "token test-token"
    assert captured["timeout"] == 60
    assert loaded.name == "remote-demo"
    assert (destination / "main.py").read_text() == 'app = "rendered"\n'


def test_fetch_template_generates_manifest_when_missing(tmp_path, monkeypatch):
    archive = _archive([("repo/main.py", b"app = 1\n")])

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, _limit):
            return archive

    from shadlet.templates import github

    monkeypatch.setattr(
        github.urllib.request, "urlopen", lambda *_args, **_kwargs: Response()
    )
    destination = tmp_path / "remote"
    manifest = fetch_template("owner/repo", destination)

    assert manifest.name == "owner-repo"
    assert (
        TemplateManifest.from_toml(
            (destination / "shadlet-template.toml").read_text()
        ).name
        == manifest.name
    )


def test_validate_template_directory(tmp_path):
    (tmp_path / "shadlet-template.toml").write_text(
        '[template]\nname = "x"\n', encoding="utf-8"
    )
    assert validate_template_directory(tmp_path) == []
    (tmp_path / "link").symlink_to("/tmp")
    errors = validate_template_directory(tmp_path)
    assert any("symlink" in e for e in errors)


def test_validate_template_directory_reports_malformed_toml(tmp_path):
    (tmp_path / "shadlet-template.toml").write_text("[template\n", encoding="utf-8")
    errors = validate_template_directory(tmp_path)
    assert any("invalid TOML" in error for error in errors)


@pytest.mark.parametrize("template", ["minimal", "dashboard", "landing-page"])
def test_create_renders_builtin_template_metadata_and_variables(tmp_path, template):
    destination = tmp_path / "custom-project"
    result = CliRunner().invoke(
        cli_app,
        [
            "create",
            "custom-project",
            "--template",
            template,
            "--target",
            str(destination),
            "--var",
            "title=Custom title",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "0.4.0" in result.output
    assert "shadlet" in result.output
    assert "starter" in result.output
    assert "Custom title" in (destination / "main.py").read_text(encoding="utf-8")
    assert "custom-project" in (destination / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert (destination / "shadlet-template.toml").is_file()


def test_create_rejects_unknown_variable_before_creating_destination(tmp_path):
    destination = tmp_path / "custom-project"
    result = CliRunner().invoke(
        cli_app,
        [
            "create",
            "custom-project",
            "--target",
            str(destination),
            "--var",
            "unknown=value",
        ],
    )
    assert result.exit_code == 1
    assert "does not declare variable" in result.output
    assert not destination.exists()


def test_create_accepts_repeated_variable_overrides(tmp_path):
    destination = tmp_path / "custom-project"
    result = CliRunner().invoke(
        cli_app,
        [
            "create",
            "custom-project",
            "--target",
            str(destination),
            "--var",
            "title=Custom title",
            "--var",
            "project_name=explicit-name",
        ],
    )
    assert result.exit_code == 0, result.output
    assert 'name = "explicit-name"' in (destination / "pyproject.toml").read_text(
        encoding="utf-8"
    )


def test_create_enforces_minimum_version_and_removes_partial_output(
    tmp_path, monkeypatch
):
    import shadlet.version

    monkeypatch.setattr(shadlet.version, "__version__", "0.2.0")
    destination = tmp_path / "incompatible"
    result = CliRunner().invoke(
        cli_app,
        ["create", "incompatible", "--target", str(destination)],
    )
    assert result.exit_code == 1
    assert "requires shadlet>=0.4.0" in result.output
    assert not destination.exists()


def test_extension_create_and_check_validates_packaged_assets(tmp_path):
    destination = tmp_path / "browser-demo"
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        [
            "extension",
            "create",
            "browser-demo",
            "--target",
            str(destination),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (destination / "pyproject.toml").is_file()
    assert (destination / "src" / "browser_demo" / "__init__.py").is_file()
    assert (destination / "src" / "index.ts").is_file()
    assert (destination / "vite.config.ts").is_file()

    assets = destination / "src" / "browser_demo" / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("window.shadlet.loadExtension({});")
    (assets / "styles.css").write_text(".browser-demo-notice {}")
    checked = runner.invoke(cli_app, ["extension", "check", str(destination)])
    assert checked.exit_code == 0, checked.output
    assert "browser-demo 0.1.0" in checked.output


def test_extension_create_rejects_invalid_name_and_existing_target(tmp_path):
    runner = CliRunner()
    invalid = runner.invoke(
        cli_app,
        ["extension", "create", "Bad-Name", "--target", str(tmp_path / "bad")],
    )
    assert invalid.exit_code == 1
    assert not (tmp_path / "bad").exists()

    destination = tmp_path / "existing"
    destination.mkdir()
    result = runner.invoke(
        cli_app,
        ["extension", "create", "valid", "--target", str(destination)],
    )
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_default_manifest_quotes_name_as_valid_toml():
    manifest = TemplateManifest(name="demo", description='description with "quotes"')
    rendered = _render_default_manifest(manifest)
    parsed = TemplateManifest.from_toml(rendered)
    assert parsed.description == manifest.description
