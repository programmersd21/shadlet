from pathlib import Path

import shadlet as ui

app = ui.App("Local storage")
storage = ui.LocalStorage(Path(__file__).parent / "data", max_bytes=100_000)
NOTE_KEY = "notes/hello.txt"


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    text = ctx.state(
        storage.read(NOTE_KEY).decode("utf-8") if storage.exists(NOTE_KEY) else "",
        key="note-text",
    )
    saved = ctx.state(storage.exists(NOTE_KEY), key="note-saved")
    message = ctx.state("", key="note-message")

    def update_text(event: ui.ChangeEvent) -> None:
        text.value = event.value

    def save(event: ui.ClickEvent) -> None:
        try:
            stored = storage.write(NOTE_KEY, text.value.encode("utf-8"), overwrite=True)
        except (OSError, UnicodeError, ui.StorageError) as error:
            message.value = str(error)
            return
        saved.value = True
        message.value = f"Saved {stored.size} bytes to {stored.key}."

    def delete(event: ui.ClickEvent) -> None:
        storage.delete(NOTE_KEY)
        saved.value = False
        message.value = "Saved note deleted."

    return ui.Center(
        ui.Column(
            ui.Heading("Local file storage", level=1),
            ui.Text("This note survives a server restart on this machine."),
            ui.Field(
                ui.Textarea(
                    value=text.value,
                    name="note",
                    rows=6,
                    on_change=update_text,
                ),
                label="Note",
            ),
            ui.Row(
                ui.Button("Save", on_click=save),
                ui.Button(
                    "Delete",
                    variant="outline",
                    on_click=delete,
                    disabled=not saved.value,
                ),
                gap=8,
            ),
            ui.Text(message.value) if message.value else None,
            gap=16,
            max_width=640,
            padding=24,
        ),
        min_height="100vh",
        padding=24,
    )


if __name__ == "__main__":
    app.run()
