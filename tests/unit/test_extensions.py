import pytest
import shadlet as ui
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient


def test_extension_manifest_is_advertised_and_assets_are_served(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("window.shadlet.loadExtension({});")
    (assets / "style.css").write_text(".extension { color: red; }")
    extension = ui.ExtensionManifest(
        name="sample",
        version="1.2.3",
        assets=assets,
        stylesheet="style.css",
    )
    app = ui.App()
    app.add_extension(extension)
    client = TestClient(create_web_app(app))

    script = client.get(extension.entry_url)
    assert extension.stylesheet_url is not None
    style = client.get(extension.stylesheet_url)
    assert script.status_code == 200
    assert script.text == "window.shadlet.loadExtension({});"
    assert style.status_code == 200
    assert style.text == ".extension { color: red; }"

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {
                "type": "hello",
                "protocol_min": 2,
                "protocol_max": 2,
                "path": "/",
            }
        )
        init = websocket.receive_json()
    assert init["extensions"][0]["name"] == "sample"
    assert init["extensions"][0]["entry_url"] == extension.entry_url


@pytest.mark.parametrize(
    "path",
    ["../index.js", "/index.js", "assets\\index.js", "assets//index.js"],
)
def test_extension_manifest_rejects_unsafe_asset_paths(tmp_path, path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("")
    with pytest.raises(ValueError, match="invalid extension asset path"):
        ui.ExtensionManifest("sample", "1.0.0", assets, entrypoint=path)


def test_extension_manifest_rejects_missing_entrypoint(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    with pytest.raises(ValueError, match="entrypoint not found"):
        ui.ExtensionManifest("sample", "1.0.0", assets)


def test_extension_asset_endpoint_rejects_traversal(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("")
    app = ui.App()
    app.add_extension(ui.ExtensionManifest("sample", "1.0.0", assets))
    client = TestClient(create_web_app(app))
    response = client.get("/_shadlet_extensions/sample/%2e%2e/secret.txt")
    assert response.status_code == 404


def test_extension_manifest_validates_metadata(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("")
    manifest = ui.ExtensionManifest(
        "sample",
        "1.0.0",
        assets,
        description="adds a notice",
        requires_shadlet=">=0.5.0,<0.6.0",
        components=("Notice", "Banner"),
    )
    assert manifest.description == "adds a notice"
    assert manifest.requires_shadlet == ">=0.5.0,<0.6.0"
    assert manifest.components == ("Notice", "Banner")

    with pytest.raises(ValueError, match="description"):
        ui.ExtensionManifest("sample", "1.0.0", assets, description="x" * 501)
    with pytest.raises(ValueError, match="requires_shadlet"):
        ui.ExtensionManifest("sample", "1.0.0", assets, requires_shadlet=">=1; rm")
    with pytest.raises(ValueError, match="components"):
        ui.ExtensionManifest("sample", "1.0.0", assets, components=("notice",))
    with pytest.raises(ValueError, match="components"):
        ui.ExtensionManifest("sample", "1.0.0", assets, components=("Notice", "Notice"))


def test_extension_manifest_rejects_symlink_escape(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    outside = tmp_path / "outside.js"
    outside.write_text("secret")
    try:
        (assets / "index.js").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available on this platform")
    with pytest.raises((ValueError, FileNotFoundError)):
        ui.ExtensionManifest("sample", "1.0.0", assets)
