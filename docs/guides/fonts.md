# custom fonts

shadlet supports custom font registration from Python. Registered fonts are
validated, converted to `@font-face` CSS and delivered to the renderer during
the initial session handshake.

## register a font

```python
import shadlet as ui

app = ui.App("typed app")

app.fonts.register(
    "Inter",
    source="/fonts/inter-variable.woff2",
    weight="100 900",
    style="normal",
    display="swap",
    preload=True,
)
```

Supported formats are WOFF2, WOFF, TTF and OTF.

## configure typography

```python
app.theme.configure(
    font_family="Inter",
    heading_font="Geist",
    mono_font_family="Geist Mono",
)
```

The generated CSS variables are:

- `--font-sans`
- `--font-heading`
- `--font-ui`
- `--font-mono`

## font options

`register` accepts:

- `weight`: a single weight or ascending variable range such as `"100 900"`
- `style`: `normal`, `italic` or `oblique`
- `display`: `auto`, `block`, `swap`, `fallback` or `optional`
- `fallback`: a string or sequence of fallback family names
- `subsets`: a string or sequence of subset names
- `unicode_range`: a CSS unicode-range value
- `feature_settings`: a CSS font-feature-settings value
- `variation_settings`: a CSS font-variation-settings value
- `preload`: preload only fonts marked as critical
- `alias`: an additional family name for the same face

## generated css

```python
print(app.fonts.css())
print(app.theme.css_variables())
```

## security notes

- Font source paths are validated and traversal segments are rejected.
- Remote sources are not fetched by the Python runtime; the browser loads them.
- CSS strings and family names are escaped before rendering.
- Only fonts with `preload=True` are added as preload links.
