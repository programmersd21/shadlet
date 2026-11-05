# icons

shadlet ships the complete [Lucide](https://lucide.dev) icon catalogue. the
names and SVG shapes are generated from the pinned `lucide-react` package at
build time, so Python validation, aliases, and browser rendering stay in sync.

## render an icon

```python
import shadlet as ui

ui.Icon("arrow-up-right", size=18, label="open in new tab")
ui.icons.arrow_up_right(size=18, label="open in new tab")
```

`ui.icons` converts underscores to hyphens, so `ui.icons.arrow_up_right`
renders `arrow-up-right`. The namespace supports every generated Lucide name,
including aliases.

Use `label` when the icon conveys meaning on its own. Decorative icons should
omit `label`; they are hidden from assistive technology.

## buttons and menus

```python
ui.Button("save", icon="check")
ui.Button("publish", icon="upload", loading=True)
ui.SidebarItem("settings", icon="settings", href="/settings")
```

`Button(icon=...)` validates the name when the component is created. Invalid
names raise `ui.ComponentError`; the renderer never substitutes an unrelated
icon.

## discover names

```python
import shadlet as ui

print(ui.LUCIDE_VERSION)
print(ui.ICON_NAMES[:5])
print([name for name in dir(ui.icons) if "arrow" in name][:10])
```

`ICON_NAMES` is an immutable, generated tuple of canonical kebab-case names.
`dir(ui.icons)` lists the Python-safe underscore aliases.

## regenerate the catalogue

Regenerate from `packages/renderer` after updating the pinned `lucide-react`
version:

```bash
npm install
npm run generate:icons
npm run format:check
```

The command updates both the lazy renderer payload and the Python name
registry. Node.js is only needed for maintainers; applications using a built
wheel do not need Node.js or npm.
