# Multipart uploads

```console
cd examples/uploads
python main.py
```

The page documents a bounded multipart endpoint. Send a file using curl from
another terminal:

```console
curl -F "source=@report.csv" -F "category=monthly" http://127.0.0.1:8000/api/import
```

On PowerShell, use `curl.exe` if `curl` resolves to the `Invoke-WebRequest`
alias. The endpoint only reports metadata and does not persist upload bytes.
Validate file contents before using them in a real application.
