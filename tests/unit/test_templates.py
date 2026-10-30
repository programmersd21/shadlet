import pytest
from shadlet.templates.github import (
    TemplateError,
    TemplateManifest,
    parse_template_ref,
    validate_template_directory,
)


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


def test_manifest_round_trip():
    text = """
[template]
name = "demo"
version = "1.0.0"
author = "me"
min_shadlet = "0.1.0"

[dependencies]
python = ["shadlet>=0.1.0"]
npm = ["recharts"]

[variables]
title = "Demo"
"""
    manifest = TemplateManifest.from_toml(text)
    assert manifest.name == "demo"
    assert manifest.python_dependencies == ("shadlet>=0.1.0",)
    assert manifest.npm_dependencies == ("recharts",)
    assert manifest.variables == {"title": "Demo"}


def test_manifest_rejects_bad_name():
    with pytest.raises(TemplateError):
        TemplateManifest.from_toml('[template]\nname = "bad/name"\n')


def test_validate_template_directory(tmp_path):
    (tmp_path / "shadlet-template.toml").write_text('[template]\nname = "x"\n')
    assert validate_template_directory(tmp_path) == []
    (tmp_path / "link").symlink_to("/tmp")
    errors = validate_template_directory(tmp_path)
    assert any("symlink" in e for e in errors)
