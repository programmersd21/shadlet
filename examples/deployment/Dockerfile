FROM node:24-bookworm-slim AS renderer

WORKDIR /workspace/packages/renderer
COPY packages/renderer/package.json packages/renderer/package-lock.json ./
RUN npm ci
COPY packages/renderer/ ./
RUN npm run build

FROM python:3.11-slim AS dependencies

WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
COPY packages/python/shadlet ./packages/python/shadlet
COPY templates ./templates
COPY THIRD_PARTY_NOTICES.md ./
COPY --from=renderer /workspace/packages/renderer/dist ./packages/renderer/dist
RUN python -m pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-editable

FROM python:3.11-slim

ENV PATH="/workspace/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY --from=dependencies /workspace/.venv /workspace/.venv
COPY examples/deployment/main.py /workspace/main.py
RUN useradd --system --uid 10001 shadlet
USER shadlet
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.getenv('PORT', '8000')}/healthz\", timeout=2).read()"
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
