# first app

create a project:

```bash
shadlet create my-app
cd my-app
```

edit `main.py`:

```python
import shadlet as ui

app = ui.App("counter")


@app.page("/")
def home(ctx: ui.Context):
    count = ctx.state(0, key="count")

    def increment(event: ui.ClickEvent):
        count.value += 1

    return ui.Center(
        ui.Column(
            ui.Heading("counter"),
            ui.Text(count),
            ui.Button("increment", on_click=increment),
            gap=16,
        ),
        min_height="100vh",
    )


if __name__ == "__main__":
    app.run()
```

run:

```bash
shadlet dev
```

open `http://127.0.0.1:8000`.

## what happens

1. the python process starts a starlette server.
2. the browser loads the react renderer.
3. the renderer connects over websocket.
4. python renders the component tree and sends it as json.
5. clicks invoke the registered python callback.
6. state updates patch the ui without a full reload.
