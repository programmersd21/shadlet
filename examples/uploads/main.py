import shadlet as ui
from starlette.responses import JSONResponse

app = ui.App("Multipart uploads")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    return ui.Center(
        ui.Column(
            ui.Heading("Bounded multipart uploads", level=1),
            ui.Text(
                "This app accepts one small CSV file at /api/import and returns metadata."
            ),
            ui.CodeBlock(
                'curl -F "source=@report.csv" -F "category=monthly" '
                "http://127.0.0.1:8000/api/import",
                language="shell",
                line_numbers=False,
            ),
            ui.Alert(
                "Uploads are buffered only up to the configured limit. "
                "This demo does not store or inspect file contents."
            ),
            gap=16,
            max_width=720,
            padding=24,
        ),
        min_height="100vh",
        padding=24,
    )


@app.upload("/api/import", max_bytes=1_000_000)
async def import_file(request: ui.UploadRequest) -> dict[str, object] | JSONResponse:
    files = request.files.get("source", ())
    if len(files) != 1:
        return JSONResponse(
            {"error": "upload exactly one file in the 'source' field"}, status_code=400
        )
    source = files[0]
    if not source.filename.lower().endswith(".csv"):
        return JSONResponse(
            {"error": "the source file must have a .csv filename"}, status_code=400
        )
    return {
        "filename": source.safe_filename,
        "size": source.size,
        "content_type": source.content_type,
        "category": request.fields.get("category", "uncategorized"),
    }


if __name__ == "__main__":
    app.run()
