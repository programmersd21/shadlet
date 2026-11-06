import asyncio
import io
import runpy
import subprocess
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
    try:
        (tmp_path / "link").symlink_to("/tmp")
    except OSError as error:
        pytest.skip(f"symlinks are not available on this platform: {error}")
    errors = validate_template_directory(tmp_path)
    assert any("symlink" in e for e in errors)


def test_validate_template_directory_reports_malformed_toml(tmp_path):
    (tmp_path / "shadlet-template.toml").write_text("[template\n", encoding="utf-8")
    errors = validate_template_directory(tmp_path)
    assert any("invalid TOML" in error for error in errors)


@pytest.mark.parametrize(
    "template", ["minimal", "dashboard", "landing-page", "settings", "auth", "crud"]
)
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
    expected_template_version = "0.7.0"
    assert expected_template_version in result.output
    assert "shadlet" in result.output
    assert "starter" in result.output
    assert "Custom title" in (destination / "main.py").read_text(encoding="utf-8")
    assert "custom-project" in (destination / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert (destination / "shadlet-template.toml").is_file()


def test_settings_template_builds_page_tree():
    import shadlet as ui
    from shadlet.app.context import Context
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/settings/main.py")["app"]

    async def send_json(_message):
        return None

    session = Session(app, send_json=send_json)
    match = app.match("/")
    context = Context(session, match)
    page = asyncio.run(app.render_page(match, context))
    assert isinstance(page, ui.Component)
    assert page.type == "Column"


def test_settings_switch_change_updates_session_state():
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/settings/main.py")["app"]
    messages = []

    async def send_json(message):
        messages.append(message)

    async def exercise():
        session = Session(app, send_json=send_json)
        await session.send_init()
        initial = messages[-1]["tree"]

        def find_switch(node):
            if (
                node["type"] == "Switch"
                and node["props"].get("label") == "Product updates"
            ):
                return node
            for child in node["children"]:
                found = find_switch(child)
                if found is not None:
                    return found
            for children in node["slots"].values():
                for child in children:
                    found = find_switch(child)
                    if found is not None:
                        return found
            return None

        switch = find_switch(initial)
        assert switch is not None
        await session.handle_event(
            switch["events"]["change"], {"value": False, "checked": False}, seq=1
        )
        update = messages[-1]
        assert update["type"] == "update"
        assert {
            "op": "set",
            "key": "/:product_updates",
            "value": False,
        } in update["state_patches"]

    asyncio.run(exercise())


def test_landing_template_has_complete_sections_and_valid_fragment_links():
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/landing-page/main.py")["app"]
    messages = []

    async def send_json(message):
        messages.append(message)

    async def exercise():
        session = Session(app, send_json=send_json)
        await session.send_init()
        tree = messages[-1]["tree"]
        ids = set()
        fragments = set()

        def visit(node):
            element_id = node["props"].get("id")
            if element_id:
                ids.add(element_id)
            href = node["props"].get("href")
            if isinstance(href, str) and href.startswith("#"):
                fragments.add(href[1:])
            for child in node["children"]:
                visit(child)
            for children in node["slots"].values():
                for child in children:
                    visit(child)

        visit(tree)
        assert {"top", "features", "use-cases", "pricing", "faq"}.issubset(ids)
        assert fragments.issubset(ids)

    asyncio.run(exercise())


@pytest.mark.parametrize("template", ["auth", "crud"])
def test_application_template_routes_render(template):
    import shadlet as ui
    from shadlet.app.context import Context
    from shadlet.runtime.session import Session

    app = runpy.run_path(f"templates/{template}/main.py")["app"]

    async def send_json(_message):
        return None

    session = Session(app, send_json=send_json)
    for route in app.routes():
        match = app.match(route.path)
        page = asyncio.run(app.render_page(match, Context(session, match)))
        assert isinstance(page, ui.Component), route.path


def test_auth_template_login_validation_and_success():
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/auth/main.py")["app"]
    messages = []

    async def send_json(message):
        messages.append(message)

    async def exercise():
        session = Session(app, send_json=send_json)
        await session.send_init()
        events = session.event_registry.snapshot_ids()
        submit_id = next(
            event_id
            for event_id, binding in events.items()
            if binding["event"] == "click"
        )
        await session.handle_event(submit_id, {}, seq=1)
        assert session.state_store.snapshot()["/:error"].startswith("Enter an email")

        await session.send_init()
        events = session.event_registry.snapshot_ids()
        input_ids = [
            event_id
            for event_id, binding in events.items()
            if binding["event"] == "change"
        ]
        await session.handle_event(input_ids[0], {"value": "user@example.com"}, seq=2)
        await session.handle_event(input_ids[1], {"value": "password123"}, seq=3)
        await session.send_init()
        submit_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click"
        )
        await session.handle_event(submit_id, {}, seq=4)
        assert session.state_store.snapshot()["/:authenticated"] is True

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("route", "email_key", "error_key", "sent_key"),
    [
        (
            "/reset",
            "/reset:reset_email",
            "/reset:reset_error",
            "/reset:reset_sent",
        )
    ],
)
def test_auth_template_reset_validates_before_feedback(
    route, email_key, error_key, sent_key
):
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/auth/main.py")["app"]

    async def send_json(_message):
        return None

    async def exercise():
        session = Session(app, send_json=send_json)
        session.route = app.match(route)
        await session.send_init()
        email_change = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "change"
        )
        await session.handle_event(email_change, {"value": "invalid"}, seq=1)
        submit = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click"
        )
        await session.handle_event(submit, {}, seq=2)
        assert (
            session.state_store.snapshot()[error_key] == "Enter a valid email address."
        )
        assert session.state_store.snapshot()[sent_key] is False
        await session.send_init()
        email_change = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "change"
        )
        await session.handle_event(email_change, {"value": "user@example.com"}, seq=3)
        await session.send_init()
        submit = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click"
        )
        await session.handle_event(submit, {}, seq=4)
        assert session.state_store.snapshot()[sent_key] is True
        assert session.state_store.snapshot()[email_key] == "user@example.com"

    asyncio.run(exercise())


def test_crud_template_create_edit_delete_session_records():
    from shadlet.runtime.session import Session

    app = runpy.run_path("templates/crud/main.py")["app"]

    async def send_json(_message):
        return None

    async def exercise():
        session = Session(app, send_json=send_json)
        await session.send_init()

        select_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "row_click"
        )
        await session.handle_event(
            select_id,
            {
                "value": {
                    "id": "prj_001",
                    "name": "Website refresh",
                    "status": "In progress",
                }
            },
            seq=2,
        )
        snapshot = session.state_store.snapshot()
        assert snapshot["/:selected_id"] == "prj_001"

        await session.send_init()
        edit_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"] == "r.3.1"
        )
        await session.handle_event(edit_id, {"value": "prj_001"}, seq=3)
        assert session.state_store.snapshot()["/:dialog_open"] is True
        assert session.state_store.snapshot()["/:project_name"] == "Website refresh"

        await session.send_init()
        change_ids = [
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "change"
        ]
        await session.handle_event(change_ids[0], {"value": "Renamed"}, seq=4)
        await session.send_init()
        save_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"].endswith("@footer.0")
        )
        await session.handle_event(save_id, {}, seq=5)
        assert session.state_store.snapshot()["/:projects"][0]["name"] == "Renamed"

        await session.send_init()
        delete_button_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"].endswith(".2")
        )
        await session.handle_event(delete_button_id, {"value": "prj_001"}, seq=6)
        await session.send_init()
        confirm_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"].endswith("@action.0")
        )
        await session.handle_event(confirm_id, {}, seq=7)
        assert all(
            row["id"] != "prj_001"
            for row in session.state_store.snapshot()["/:projects"]
        )

        await session.send_init()
        create_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"] == "r.0.1"
        )
        await session.handle_event(create_id, {}, seq=8)
        await session.send_init()
        change_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "change"
        )
        await session.handle_event(change_id, {"value": "New item"}, seq=9)
        await session.send_init()
        save_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "click" and binding["node"].endswith("@footer.0")
        )
        await session.handle_event(save_id, {}, seq=10)
        assert any(
            row["id"] == "prj_007" and row["name"] == "New item"
            for row in session.state_store.snapshot()["/:projects"]
        )

        await session.send_init()
        query_id = next(
            event_id
            for event_id, binding in session.event_registry.snapshot_ids().items()
            if binding["event"] == "query_change"
        )
        await session.handle_event(
            query_id,
            {
                "values": {
                    "page_index": 0,
                    "page_size": 5,
                    "sorting": [{"key": "name", "direction": "asc"}],
                    "search": "mobile",
                    "filters": {},
                }
            },
            seq=11,
        )
        assert session.state_store.snapshot()["/:search"] == "mobile"

    asyncio.run(exercise())


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
    assert "requires shadlet>=0.7.0" in result.output
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


def test_extension_info_and_build_commands(tmp_path, monkeypatch):
    destination = tmp_path / "browser-info"
    runner = CliRunner()
    created = runner.invoke(
        cli_app,
        ["extension", "create", "browser-info", "--target", str(destination)],
    )
    assert created.exit_code == 0, created.output

    assets = destination / "src" / "browser_info" / "assets"

    def fake_run(args, cwd=None, check=False):
        if args[-2:] == ["run", "build"]:
            assets.mkdir(parents=True, exist_ok=True)
            (assets / "index.js").write_text("window.shadlet.loadExtension({});")
            (assets / "styles.css").write_text(".notice {}")
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr("shadlet.cli.extensions.shutil.which", lambda _: "npm")
    monkeypatch.setattr("shadlet.cli.extensions.subprocess.run", fake_run)
    built = runner.invoke(cli_app, ["extension", "build", str(destination)])
    assert built.exit_code == 0, built.output
    assert (assets / "index.js").is_file()

    informed = runner.invoke(cli_app, ["extension", "info", str(destination)])
    assert informed.exit_code == 0, informed.output
    assert "browser-info" in informed.output
    assert "0.1.0" in informed.output
    assert "Notice" in informed.output
