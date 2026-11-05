# Shadlet examples

Runnable samples for the framework's main application patterns. Start with the
counter, then follow the topics that match your app. Every sample has its own
`README.md` with the command to run it and the Shadlet concepts it demonstrates.

## Run from a source checkout

Install Shadlet and its Python dependencies once from the repository root:

```console
python -m pip install -e .
```

Then run an example from its directory:

```console
cd examples/counter
python main.py
```

The server prints its local URL. Stop it with `Ctrl+C`. The renderer is already
bundled with Shadlet; Node.js is not needed to run these examples.

## Learning path

| Example | Learn |
| --- | --- |
| [counter](counter/) | App startup, page rendering, session state, click events |
| [todo](todo/) | Forms, input state, validation, adding and removing rows |
| [components](components/) | Composition, fields, overlays, tabs, accordions, feedback |
| [layouts](layouts/) | Responsive layouts, semantic sections, themes, fragment links |
| [routing](routing/) | Path parameters, navigation, query state, not-found pages |
| [forms](forms/) | Pydantic validation and accessible field errors |
| [data-table](data-table/) | Server-side search, filters, sorting, pagination, row selection |
| [charts](charts/) | Chart types, series, theme toggle, empty-data presentation |
| [background-tasks](background-tasks/) | Session-owned async work and progress updates |
| [storage](storage/) | Safe local file storage and reactive UI state |
| [uploads](uploads/) | Bounded multipart HTTP endpoints and file validation |
| [icons-demo](icons-demo/) | Named icons, icon namespace, button icons |
| [dashboard](dashboard/) | A small multi-page admin-style application |
| [deployment](deployment/) | Container deployment; see the deployment guide |

For a larger starter with create/edit/delete flows, use the packaged
[`crud` template](../templates/crud/). For a profile settings UI and a
non-production authentication flow, see the [`settings`](../templates/settings/)
and [`auth`](../templates/auth/) templates.

## Project boundaries

Examples use in-memory data unless a page explicitly demonstrates local file
storage. They are learning material, not production authentication, database,
or job-queue implementations. Read each example's notes before adapting it to
production.
