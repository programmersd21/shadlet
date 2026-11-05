# http uploads

register multipart `post` endpoints with `App.upload`. the handler receives
bounded file bytes and text fields through `UploadRequest`; successful results
are returned as json unless the handler returns a Starlette `Response`.

```python
import shadlet as ui

app = ui.App()


@app.upload("/api/import", max_bytes=2_000_000)
async def import_file(request: ui.UploadRequest):
    source = request.files["source"][0]
    return {
        "filename": source.filename,
        "size": source.size,
        "category": request.fields.get("category"),
    }
```

`UploadRequest.files` maps each multipart field name to a tuple because a form
may include multiple files for one field. each `UploadedFile` contains
`filename`, `content_type`, `data`, and `size`. handlers should validate content
and filenames before storing data; filenames are untrusted metadata.

`WebConfig.max_upload_bytes` sets the application-wide file-byte limit (10 mb
by default); the endpoint's `max_bytes` can lower it. the request body is
stream-limited with a small allowance for multipart framing and fields. invalid
multipart input returns `400`, oversized uploads return `413`, rejected origins
return `403`, and failed authentication returns `401`. when `App.authenticate`
is configured, it also protects upload routes; an optional bearer token is
passed as `ConnectionRequest.token`.

upload requests follow the app's origin policy. configure allowed origins and
authentication for deployments that accept requests from other sites. file
contents are buffered only up to the configured per-request bound and should
not be treated as durable storage.
