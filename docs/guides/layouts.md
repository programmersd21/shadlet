# layouts

layouts use css flexbox and grid. no custom layout engine is implemented.

## available

- `Row`, `Column`, `Stack`, `Grid`, `Container`, `Center`, `Spacer`, `Wrap`, `Positioned`, `Expanded`, `SizedBox`, `ScrollArea`, `Box`, `GridItem`.

## responsive values

```python
ui.Grid(columns=ui.Responsive(base=1, sm=2, lg=3))
```

## css escape hatch

pass `style` as a mapping or `class_name` for custom css.

```python
ui.Box(style={"backgroundColor": "red"}, class_name="my-box")
```

`Box`, `Grid`, and text components accept `as_` for semantic HTML tags. Layouts
also accept `id` so in-page links can target a section:

```python
ui.Link("Plans", href="#pricing")
ui.Box(ui.Heading("Plans"), as_="section", id="pricing")
```

The Python argument is named `as_` because `as` is reserved in Python; it is
serialized as the renderer's `as` prop.
