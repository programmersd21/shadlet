import base64
import hashlib
import importlib
import sys
import zipfile
from pathlib import Path

from shadlet import App
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient


def _write_wheel(path: Path) -> None:
    package_files = {
        "sample_extension/__init__.py": (
            "from importlib.resources import files\n"
            "from shadlet.extensions import ExtensionManifest\n"
            "def extension():\n"
            "    return ExtensionManifest(\n"
            "        name='sample', version='1.0.0',\n"
            "        assets=files(__package__) / 'assets',\n"
            "        entrypoint='index.js', stylesheet='index.css',\n"
            "    )\n"
        ),
        "sample_extension/assets/index.js": (
            "window.shadlet.loadExtension({name:'sample',version:'1.0.0',"
            "components:{Notice:({props})=>window.React.createElement('aside',"
            "{className:'sample-notice'},String(props.message))}});"
        ),
        "sample_extension/assets/index.css": ".sample-notice{display:block}",
        "sample_extension-1.0.0.dist-info/METADATA": (
            "Metadata-Version: 2.1\nName: sample-extension\nVersion: 1.0.0\n"
        ),
        "sample_extension-1.0.0.dist-info/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: shadlet-test\nRoot-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ),
        "sample_extension-1.0.0.dist-info/entry_points.txt": (
            "[shadlet.extensions]\nsample = sample_extension:extension\n"
        ),
    }
    dist_info = "sample_extension-1.0.0.dist-info"
    records = []
    with zipfile.ZipFile(path, "w") as wheel:
        for name, content in package_files.items():
            data = content.encode()
            wheel.writestr(name, data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest())
            records.append(f"{name},sha256={digest.rstrip(b'=').decode()},{len(data)}")
        records.append(f"{dist_info}/RECORD,,")
        wheel.writestr(f"{dist_info}/RECORD", "\n".join(records) + "\n")


def test_installed_extension_wheel_loads_without_node(tmp_path, monkeypatch):
    wheel_path = tmp_path / "sample_extension-1.0.0-py3-none-any.whl"
    install_path = tmp_path / "site-packages"
    install_path.mkdir()
    _write_wheel(wheel_path)
    with zipfile.ZipFile(wheel_path) as wheel:
        wheel.extractall(install_path)
    monkeypatch.syspath_prepend(str(install_path))
    importlib.invalidate_caches()
    monkeypatch.delitem(sys.modules, "sample_extension", raising=False)

    app = App()
    client = TestClient(create_web_app(app))
    response = client.get("/_shadlet_extensions/sample/index.js")

    assert response.status_code == 200
    assert "window.shadlet.loadExtension" in response.text
    assert client.get("/_shadlet_extensions/sample/index.css").text == (
        ".sample-notice{display:block}"
    )
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {
                "type": "hello",
                "protocol_min": 2,
                "protocol_max": 2,
                "path": "/",
                "platform": "web",
            }
        )
        init = websocket.receive_json()
    assert init["extensions"] == [
        {
            "name": "sample",
            "version": "1.0.0",
            "entry_url": "/_shadlet_extensions/sample/index.js",
            "stylesheet_url": "/_shadlet_extensions/sample/index.css",
        }
    ]
