# Server-side data table

```console
cd examples/data-table
python main.py
```

Search, filter by team, sort columns, paginate, and select rows. The example
keeps a small dataset in memory so the query callback is easy to follow. In a
real application, translate only the validated `DataTableQuery` fields into
bounded database operations.
