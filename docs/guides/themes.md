# themes

shadlet uses css variables. light, dark and system themes are supported.

set the app theme:

```python
app = ui.App("my app", theme=ui.Theme.DARK)
```

the renderer toggles the `.dark` class on the document root.
