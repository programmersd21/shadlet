# Local storage

```console
cd examples/storage
python main.py
```

Save and delete a text note through `ui.LocalStorage`. Files are written below
`examples/storage/data`. This demonstrates local persistence only; multiple
workers do not share this directory automatically. Keep user-provided storage
keys relative and never expose filesystem paths to clients.
