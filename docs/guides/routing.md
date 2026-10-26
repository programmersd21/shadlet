# routing

register pages with `@app.page(path)`.

```python
@app.page("/users/{id}")
def user(ctx: ui.Context):
    user_id = ctx.params["id"]
    return ui.Text(f"user {user_id}")
```

dynamic segments use `{name}`. a not-found page can be registered with `@app.not_found`.
