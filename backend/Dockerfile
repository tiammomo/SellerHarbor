FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    REVIEWPILOT_PORT=38081 \
    REVIEWPILOT_DB_PATH=/data/reviewpilot.db

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

RUN mkdir -p /data

EXPOSE 38081
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD uv run --no-sync python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:38081/healthz', timeout=3).read()"

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "38081"]
