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
