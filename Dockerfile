FROM python:3.13.4-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock .

RUN pip install uv && uv venv && uv sync --frozen

FROM python:3.13.4-slim

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src"

RUN useradd -m app && \
    apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/src /data

COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml alembic.ini categories.json category_labels.es.json ./
COPY --chown=app:app src src
COPY --chown=app:app alembic alembic

USER app

CMD ["granian","--interface","asgi","--workers","2","--host","0.0.0.0","--port","9090","api.server:app"]
