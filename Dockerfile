FROM python:3.13.4-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install uv && uv venv && uv sync

FROM python:3.13.4-slim

WORKDIR /app
RUN mkdir -p /app/src

ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/src"

RUN useradd -m app && apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.venv /app/.venv

COPY pyproject.toml .
COPY alembic.ini .
COPY categories.json .
COPY src src

# Used by beat service
RUN mkdir -p /data
RUN chown -R app:app /app /data

USER app

CMD ["granian","--interface","asgi","--workers","2","--port","9090","server:app"]
