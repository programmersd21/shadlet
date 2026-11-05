# Container deployment example

This directory contains a small ASGI application used by the repository's
multi-stage Docker build. Build and run it from the repository root:

```console
docker build -f examples/deployment/Dockerfile -t shadlet-example .
docker run --rm -p 8000:8000 shadlet-example
```

The image builds the React renderer in a Node stage and packages the assets in
the Python image. Running the container does not require Node. Review the
[deployment guide](../../docs/guides/deployment.md) before adapting this sample.
