import shadlet as ui
from shadlet.web.config import WebConfig
from shadlet.web.server import create_web_app
from starlette.testclient import TestClient


def test_multipart_upload_handler_receives_file_and_fields():
    app = ui.App()
    received = []

    @app.upload("/api/upload")
    async def upload(request: ui.UploadRequest):
        file = request.files["document"][0]
        received.append((file.filename, file.content_type, file.data, request.fields))
        return {"size": file.size}

    client = TestClient(create_web_app(app))
    response = client.post(
        "/api/upload",
        data={"category": "reports"},
        files={"document": ("report.txt", b"shadlet", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"size": 7}
    assert received == [
        ("report.txt", "text/plain", b"shadlet", {"category": "reports"})
    ]


def test_upload_limit_is_enforced():
    app = ui.App(web=WebConfig(max_upload_bytes=4))

    @app.upload("/api/upload")
    async def upload(request: ui.UploadRequest):
        return {"ok": True}

    client = TestClient(create_web_app(app))
    response = client.post(
        "/api/upload",
        files={"document": ("large.txt", b"12345", "text/plain")},
    )
    assert response.status_code == 413
    assert response.json() == {"error": "upload exceeds size limit"}


def test_upload_endpoints_use_application_authentication():
    app = ui.App(authenticate=lambda request: request.token == "accepted")

    @app.upload("/api/upload")
    async def upload(request: ui.UploadRequest):
        return {"ok": True}

    client = TestClient(create_web_app(app))
    payload = {"file": ("sample.txt", b"sample", "text/plain")}
    denied = client.post("/api/upload", files=payload)
    accepted = client.post(
        "/api/upload",
        files=payload,
        headers={"Authorization": "Bearer accepted"},
    )
    assert denied.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json() == {"ok": True}
