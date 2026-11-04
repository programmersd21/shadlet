"""Small ASGI application used by the Docker and Render deployment examples."""

import shadlet as ui

app = ui.App("shadlet deployment example")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    return ui.Center(
        ui.Card(
            ui.Heading("shadlet is running", level=1),
            ui.Text("the Python runtime is serving this page over WebSocket."),
        ),
        min_height="100vh",
        padding=24,
    )
