# react component extensions

extensions are a first-class way to add application-specific react components to
shadlet without forking the renderer or asking every application to register
components in its own browser entry point. an extension is a normal python
distribution: it declares a small manifest, ships a browser bundle and any
public assets inside its wheel, and registers its component adapters through
the shadlet runtime.

this design keeps the application interface python-first while letting
extension authors use react and the browser platform where they are the right
tools. python owns the component tree, serializable properties, session state,
and event handlers. react owns the component's browser rendering and local
interaction. shadlet connects the two through its versioned protocol and an
explicit event bridge; it does not serialize python callbacks or turn the
browser into a second source of application state.

the runtime discovers installed extensions, serves their declared assets,
advertises their metadata during the websocket handshake, and loads their
styles and component registrations before rendering the page. running a shadlet
application does not require node.js or npm. extension authors need node.js 24
and a javascript toolchain to build browser bundles.

## when to create an extension

create an extension when a component needs browser behavior that is not
available in the built-in catalogue, such as a specialized visualization,
editor, map, media control, or integration with a browser-only library. keep
application-specific business rules, data access, authorization, and durable
state in python. make the browser component a focused view and interaction
surface, not an independent application with its own server contract.

before building an extension, check the [built-in component catalogue](components/catalogue.md)
and the [component composition guide](guides/components.md). prefer built-in
components when they already meet the need: they receive the same protocol,
accessibility, lifecycle, and compatibility testing as the renderer itself.

extensions are intentionally ordinary python packages rather than a separate
plugin runtime. this makes installation and deployment familiar, but it also
means extensions are trusted application code. see [security and trust](#security-and-trust)
before installing an extension you do not control.

## how the integration works

an extension connects the python and browser sides through four steps:

1. **python package metadata** declares a `shadlet.extensions` entry point.
2. **the extension manifest** identifies the namespace, version, javascript
   entry point, and optional stylesheet within the package's assets.
3. **the server handshake** includes extension names, versions, and asset urls
   in the protocol `init` message.
4. **the renderer** loads each stylesheet and javascript bundle, checks that
   the bundle registered its components, and only then renders the initial
   component tree.

the python component type and browser registration must agree. for example,
python emits `acme:Notice`, so the browser bundle registers a `Notice`
component under the `acme` namespace. the namespace prevents collisions with
built-in components and with other extensions.

extension assets are served from
`/_shadlet_extensions/{extension-name}/{asset-path}`. only assets within the
manifest's package directory are readable through this endpoint; there is no
directory listing. these are ordinary browser requests, not websocket
messages.

## package layout

start a new extension package with the cli:

```bash
shadlet extension create my-extension
cd my-extension
npm install
npm run build
shadlet extension check
python -m build
```

the generator creates Python entry-point metadata, a manifest factory, a
namespaced component, a React registration bundle, a stylesheet, a test, and
packaging instructions. `shadlet extension check` imports and calls the
declared extension factory and reads its assets, so run it only on source code
you trust. the built wheel packages the browser assets; applications that
install that wheel do not need Node.js or npm.

a small extension can use a `src` layout like this:

```text
acme-shadlet/
├── pyproject.toml
└── src/
    └── acme_shadlet/
        ├── __init__.py
        └── assets/
            ├── index.js
            └── styles.css
```

the python package exports the manifest factory. use
`importlib.resources.files` rather than a path relative to the process working
directory: the installed application may start from any directory, and the
package resources are the distribution's source of truth.

```python
from importlib.resources import files

from shadlet import ExtensionManifest


def extension() -> ExtensionManifest:
    return ExtensionManifest(
        name="acme",
        version="1.0.0",
        assets=files(__package__) / "assets",
        entrypoint="index.js",
        stylesheet="styles.css",
    )
```

an extension without a separate stylesheet can omit `stylesheet`:

```python
extension = ExtensionManifest(
    name="acme",
    version="1.0.0",
    assets=files(__package__) / "assets",
)
```

the default entry point is `index.js`. the stylesheet is optional. both paths
are relative to the assets directory.

## distribution metadata

declare the entry point in the extension distribution's `pyproject.toml`.
include the browser assets in the built wheel; a source checkout working
locally is not proof that those files are present in an installed wheel.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "acme-shadlet"
version = "1.0.0"
dependencies = ["shadlet>=0.4,<0.5"]

[project.entry-points."shadlet.extensions"]
acme = "acme_shadlet:extension"

[tool.hatch.build.targets.wheel]
packages = ["src/acme_shadlet"]

[tool.hatch.build.targets.wheel.force-include]
"src/acme_shadlet/assets" = "acme_shadlet/assets"
```

the entry-point group must be spelled exactly as
`shadlet.extensions`. its value uses python's `module:attribute` form. the
attribute may be:

- an `ExtensionManifest` instance; or
- a zero-argument callable that returns an `ExtensionManifest`.

a factory is useful when the manifest is created from package resources, as in
the example. shadlet loads installed entry points when the web application is
created, then invokes each factory once for that application. imports and
factory errors are startup errors: fix the package rather than hiding a broken
extension behind a fallback.

extensions can also be registered directly on an application. this is useful
for an application-owned extension or a small prototype that is not yet a
separate distribution:

```python
from importlib.resources import files

import shadlet as ui

app = ui.App()
app.add_extension(
    ui.ExtensionManifest(
        name="acme",
        version="1.0.0",
        assets=files("my_app") / "extension_assets",
        stylesheet="styles.css",
    )
)
```

direct registration and entry-point discovery use the same manifest validation
and asset-serving behavior. registering two manifests with the same extension
name is an error.

## manifest rules

`ExtensionManifest` validates its identity and assets when it is constructed:

- names must start with a lowercase letter and may contain lowercase letters,
  digits, hyphens, and underscores; the maximum length is 63 characters.
- versions use `major.minor.patch` semantic version form, with an optional
  prerelease suffix.
- the asset root must be a package-resource directory.
- the entry point and optional stylesheet must already exist as files.
- asset paths must be relative slash-separated paths. empty segments, `.` and
  `..`, absolute paths, and backslashes are rejected.
- for filesystem-backed asset roots, resolved symlinks may not escape the
  package's asset directory.

use a stable namespace for a published extension. changing the namespace
changes every python component type and browser component registration that
uses it, so it is an API change for applications.

## python component api

define an ordinary shadlet component whose `type` is the namespaced component
name. use regular python constructor properties for serializable data, and bind
event handlers with `bind`. callbacks must not be passed as component
properties.

```python
import shadlet as ui


class Notice(ui.Component):
    type = "acme:Notice"

    def __init__(
        self,
        message: str,
        *,
        tone: str = "info",
        on_dismiss=None,
    ) -> None:
        super().__init__(message=message, tone=tone)
        self.bind("dismiss", on_dismiss)
```

the type consists of the extension namespace, a colon, and the component name.
component names start with an uppercase letter and contain only letters and
digits. python class names and react export names do not have to be identical,
but the wire type and the registration key must match exactly.

render the component as part of a normal python page. the state and handler
remain server-side; each render sends the current value in the component props.
the [state guide](guides/state.md) covers session-scoped state in more detail.

## browser component api

the renderer calls a registered component with an adapter-props object:

| property | meaning |
|---|---|
| `props` | the serializable python properties for this component |
| `children` | rendered positional python children |
| `slots` | rendered named python slots, keyed by slot name |
| `events` | the event names bound by the python component |
| `dispatch` | sends a named event and serializable payload to its python handler |
| `navigate` | requests shadlet navigation to a path |
| `route` | the current route path |
| `nodeId` | the renderer's id for this component node |

use only what the component needs. a minimal bundle registration looks like
this:

```javascript
import React from "react";

function Notice({ props, children }) {
  const tone =
    typeof props.tone === "string" ? props.tone : "info";

  return React.createElement(
    "aside",
    { className: `acme-notice acme-notice--${tone}` },
    children ?? String(props.message ?? ""),
  );
}

window.shadlet.loadExtension({
  name: "acme",
  version: "1.0.0",
  components: { Notice },
});
```

`window.React` is the renderer's shared react instance. import `react` in the
extension source so hooks and elements use the normal react api, then
externalize that dependency in the bundle configuration below. the resulting
browser bundle uses the shared global rather than shipping a second react
runtime.

the bridge is available before extension scripts are injected. each bundle must
call `window.shadlet.loadExtension` exactly once with its matching name and
version and a non-empty `components` object. a script that loads successfully
but does not register is treated as an extension load failure.

### props and children

component properties cross the python/server boundary as json-compatible
values. use strings, finite numbers, booleans, `null`, arrays, and string-keyed
objects. shadlet also converts supported python values such as enums,
dataclasses, pydantic models, dates, and state values into wire data. callbacks,
arbitrary objects, cyclic data, and component instances are not valid props.

use positional python children for a component's main content. a browser
adapter receives those as `children`. named slots are exposed through `slots`,
with each slot name mapped to its rendered content. slots and children are
already react nodes; do not JSON-encode them or attempt to recreate them from
props.

validate dynamic values at the browser boundary. protocol data is untrusted
input from the perspective of a component: check a property's type and apply a
sensible display fallback rather than assuming every value has the expected
shape.

### events back to python

python binds a callback to an event name, and the browser adapter dispatches
that same name. payloads must be serializable data:

```python
class ColorPicker(ui.Component):
    type = "acme:ColorPicker"

    def __init__(self, value: str, *, on_change=None) -> None:
        super().__init__(value=value)
        self.bind("change", on_change)
```

```javascript
function ColorPicker({ props, dispatch }) {
  return React.createElement("input", {
    type: "color",
    value: typeof props.value === "string" ? props.value : "#000000",
    onChange: (event) => dispatch("change", { value: event.target.value }),
  });
}
```

the python callback receives a `ui.ChangeEvent` for the standard `"change"`
event name:

```python
def update_color(event: ui.ChangeEvent) -> None:
    selected_color.value = event.value
```

unknown event names arrive as the general `ui.Event`. its `name` identifies the
event, `value` exposes a conventional `value` field when present, and `raw`
contains the payload dictionary. avoid putting secrets or large application
objects in event payloads. pass only the small values needed for the server to
perform the action.

do not attach browser callbacks to `props`; callbacks cannot be serialized and
must use `dispatch`. do not put server-side python functions in a bundle or
expect browser state to mutate python state without dispatching an event.
shadlet's [events guide](guides/events.md) describes the server-side event
lifecycle.

### complete counter example

the following compact example connects a python component, a browser adapter,
and server-side state from end to end. the event string `"increment"` is the
same in the python binding and the browser dispatch.

python:

```python
import shadlet as ui


class Counter(ui.Component):
    type = "acme:Counter"

    def __init__(self, value: int, *, on_increment=None) -> None:
        super().__init__(value=value)
        self.bind("increment", on_increment)


app = ui.App("counter example")


@app.page("/")
def home(ctx: ui.Context):
    count = ctx.state(0, key="counter")

    def increment(event: ui.Event) -> None:
        count.value += 1

    return Counter(count.value, on_increment=increment)
```

browser entry:

```javascript
import React from "react";

function Counter({ props, dispatch }) {
  const value = typeof props.value === "number" ? props.value : 0;
  return React.createElement(
    "button",
    {
      type: "button",
      onClick: () => dispatch("increment"),
    },
    `count: ${value}`,
  );
}

window.shadlet.loadExtension({
  name: "acme",
  version: "1.0.0",
  components: { Counter },
});
```

when the browser button is clicked, the renderer dispatches the event id
associated with that python component. the server invokes the callback,
updates the session state, rerenders the page, and sends the changed component
tree to the browser. the adapter then receives the new `value` prop. this keeps
the durable application value on the python side while the browser owns the
button's rendering.

### browser-local state

react state is appropriate for ephemeral presentation behavior such as an
animation phase, a temporary expanded panel, or an input interaction that does
not yet represent committed application data. use python state when the value
must drive server rendering, be shared with other server-side code, or persist
across renders or reconnects.

when a user action changes application data, dispatch the meaningful action or
new value to python and render the updated value from the next server response.
do not treat a local react state copy as authoritative: it can become stale
when the server rerenders, the connection reconnects, or another event changes
the same value.

## build the browser bundle

the extension's browser code must be bundled as a self-contained iife-style
entry script that calls the bridge. do not bundle react itself. for example,
with vite:

```typescript
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    lib: {
      entry: "src/index.js",
      formats: ["iife"],
      name: "AcmeExtension",
      fileName: () => "index.js",
    },
    rollupOptions: {
      external: ["react"],
      output: { globals: { react: "React" } },
    },
  },
});
```

import the stylesheet from the browser entry so the production build emits it
alongside the javascript:

```javascript
import "./styles.css";
```

the library build may also emit a css file. copy the generated browser entry and
stylesheet into the python package's `assets` directory, using the filenames
declared by the manifest. keep output names deterministic so the manifest does
not need to be rewritten after every build.

for the simplest distribution, emit one javascript entry and one stylesheet.
if the bundle uses additional chunks, fonts, images, or other files, include
them in the wheel and ensure their emitted urls are relative to the extension
entry point so they remain under the extension asset route. verify the final
wheel rather than relying on the development server's output directory.

the `base: "./"` setting helps keep generated resource references relative.
avoid loading extension code from a third-party cdn: local, versioned package
assets make deployment reproducible and keep the extension manifest's asset
boundary meaningful.

## styling

declare one stylesheet in the manifest when the browser build emits css. shadlet
loads it before the extension javascript and before rendering the initial tree.
use a stable extension-specific prefix for class names and selectors to reduce
collisions with shadlet, other extensions, and application styles.

```css
.acme-notice {
  border-inline-start: 3px solid currentColor;
  padding: 0.75rem 1rem;
}

.acme-notice--warning {
  color: #92400e;
}
```

an extension can instead pass a `styles` string to the browser
`loadExtension` bridge for small, static styles. that string is inserted into a
style element and removed if registration fails. for reusable or substantial
styles, prefer the packaged stylesheet: it is easier to review, cache, test,
and ship with the exact extension version.

styles are global css, not a sandbox. use namespaced selectors, avoid broad
rules such as `button { ... }` or `* { ... }`, and do not assume an extension's
styles are isolated from the application.

## loading, errors, and compatibility

extension manifests are included in the websocket `init` message. the renderer
loads all advertised extension styles and scripts before showing the initial
component tree. if a stylesheet or script cannot load, if registration
metadata is invalid, or if the bundle fails to register, the runtime reports a
fatal extension loading error instead of silently rendering an incomplete
page.

after successful registration, component names are resolved as
`{namespace}:{component}`. if python emits a name that the browser did not
register, the renderer displays an unknown-component error at that node.
component rendering is also guarded by an error boundary so a render exception
does not take down the whole renderer tree.

the client/server wire protocol is versioned independently from an extension's
own version. shadlet 0.3 uses protocol version 2, which carries extension
metadata in `init`. publish an extension version that describes changes to its
python component contract, browser props, events, or required assets. keep the
manifest version identical to the version registered by the browser bundle.

extension loading currently has no dependency ordering between separate
extensions. each should register independently and must not rely on another
extension's global side effects or load timing. if two components are tightly
coupled, ship them in the same extension namespace and bundle.

## security and trust

an extension's python entry point runs inside the server process when shadlet
discovers it. its browser bundle runs in the application's page with the same
browser privileges as the application. extensions are **trusted code, not
sandboxed plugins**. installing an extension is equivalent to trusting its
python package and javascript bundle.

the asset route is public static delivery, not an authorization boundary.
anything included in an extension's assets may be fetched by a browser that can
reach the application. do not package credentials, private configuration,
source maps containing secrets, or user data as extension assets.

asset path validation prevents traversal outside the declared root, including
filesystem symlink escapes for path-backed assets. it does not audit or
sandbox the contents of javascript, css, fonts, or images. review extension
dependencies and release artifacts, pin versions in deployments, and use
normal application and infrastructure controls for access to sensitive data.
the [security architecture guide](architecture/security.md) explains the
broader runtime trust model.

## testing an extension

test the package as users install it, not just as it runs from a source tree.
a useful verification sequence is:

1. build the wheel and inspect it to confirm that the python module, entry-point
   metadata, javascript entry, stylesheet, and any referenced assets are
   present.
2. install that wheel into a clean environment with a compatible shadlet
   version; start the app from a different working directory to catch
   accidental relative-path assumptions.
3. check that a duplicate namespace, missing file, invalid asset path, or
   incorrect entry-point return value fails clearly.
4. request each declared asset from the running app and verify its status,
   content, and media type.
5. verify the websocket `init` message advertises the expected extension name,
   version, and urls.
6. render each component in a real browser; test its props, children, slots,
   styles, event payloads, and failure behavior.
7. repeat with the production bundle and wheel, rather than only the dev server.

shadlet's own tests demonstrate both sides of this contract:

- `tests/integration/test_node_free_extension.py` builds a separate wheel
  fixture, extracts it into a temporary `site-packages` directory, and checks
  entry-point discovery, asset responses, and websocket metadata using python
  alone. it does not invoke node or npm.
- `packages/renderer/e2e/runtime.spec.ts` uses playwright to verify a browser
  loads and renders an extension component and its stylesheet, handles a
  python event update, and synchronizes query-state navigation.

the node-free test verifies python packaging and runtime delivery; it does not
execute the javascript bundle. the playwright test covers actual browser
execution. both are needed for confidence across the full boundary.

## troubleshooting

| symptom | likely cause | check |
|---|---|---|
| extension does not appear in the `init` message | package is not installed in the application's environment, or its entry-point group/name is wrong | inspect the installed distribution's `shadlet.extensions` entry point and restart the app |
| app startup fails while discovering an extension | entry-point import failed, factory raised, factory returned the wrong type, or a duplicate name was registered | run the factory in the same environment and inspect the startup traceback |
| manifest construction says the entry point or stylesheet is missing | the manifest filename does not match the wheel contents | inspect the wheel and compare its asset paths with `entrypoint` and `stylesheet` |
| asset request returns 404 | wrong extension name/path, missing wheel file, or unsafe path | request the exact manifest url and verify the file is inside the declared assets directory |
| extension script loads but a component is unknown | namespace or component registration does not match the python `type` | compare the exact `namespace:Component` string on both sides |
| runtime reports that the bundle did not register | the bundle executed without calling `window.shadlet.loadExtension`, or registration threw | inspect the browser console and confirm the bridge call runs at module entry |
| extension fails with a react invalid-hook error | the bundle embedded another react copy, or hooks run outside a component render | externalize `react`, use the shared global, and call hooks only inside a react component |
| styles are missing or arrive too late | stylesheet filename is wrong, css was not included in the wheel, or the manifest omitted it | fetch the stylesheet url directly and inspect the production wheel |
| works in development but not after install | assets were not included in the wheel or output references an unavailable dev url | install the built wheel in a clean environment and check every generated asset request |
| event never reaches python | browser dispatch name does not match the name bound with `bind` | compare the event string exactly and inspect the websocket event traffic |
| component props fail to render or update | a value is not wire-serializable or the adapter assumes the wrong runtime type | keep props json-compatible and validate dynamic values in the adapter |

## current boundaries

extensions provide namespaced react components and packaged browser assets;
they do not currently provide a generator command, a dedicated extension
development server, a sandbox, or a dependency-ordering mechanism. authors
build their browser bundle with their chosen javascript toolchain and distribute
the result in a python wheel.

for the complete verified feature matrix, see [limitations](limitations.md).
