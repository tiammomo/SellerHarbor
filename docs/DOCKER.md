# Docker Components

ReviewPilot can run as separate Docker components:

- `backend`: FastAPI + LangChain + LangGraph, exposed on `38081`.
- `frontend`: Next.js standalone app, exposed on `33001`.
- `postgres`: optional future persistence component for market/product snapshots.
- `redis`: optional future task queue/cache component for crawling and image jobs.
- `minio`: optional S3-compatible object storage for product images and crawl screenshots.

The current application still uses SQLite by default. PostgreSQL, Redis, and MinIO are provided as modular infrastructure for the next data-ingestion phase.

## Quick Start

Create local env values:

```bash
cp .env.docker.example .env
```

Set `ANTHROPIC_AUTH_TOKEN` in `.env` if LLM generation is needed.

Start only the application:

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:33001`
- Backend: `http://localhost:38081`
- Health: `http://localhost:38081/healthz`

## With Infrastructure Components

Start app plus PostgreSQL, Redis, and MinIO:

```bash
docker compose --profile infra up --build
```

Infra ports:

- PostgreSQL: `localhost:35432`
- Redis: `localhost:36379`
- MinIO API: `http://localhost:39000`
- MinIO Console: `http://localhost:39001`

The `minio-init` service creates the `reviewpilot-assets` bucket automatically.

## LLM Proxy

The backend container defaults to:

```text
ANTHROPIC_BASE_URL=http://host.docker.internal:17878
ANTHROPIC_MODEL=mimo-v2.5-pro
```

On Linux, `docker-compose.yml` maps `host.docker.internal` to the host gateway through `extra_hosts`, so the container can call a local model proxy running on the host.

## Data Volumes

Named volumes:

- `reviewpilot-backend-data`: SQLite database for the current MVP.
- `reviewpilot-postgres-data`: optional PostgreSQL data.
- `reviewpilot-redis-data`: optional Redis append-only data.
- `reviewpilot-minio-data`: optional object storage data.

Reset local Docker data:

```bash
docker compose down -v
```

## Component Boundaries

The Docker layout intentionally keeps responsibilities separate:

- Backend owns API, LangGraph generation, product sourcing reports, and future crawler orchestration.
- Frontend owns UI and calls the backend through `NEXT_PUBLIC_API_BASE_URL`.
- PostgreSQL will own normalized product/source/snapshot metadata.
- Redis will own async job queues and short-lived crawling locks.
- MinIO/R2-compatible storage will own product images, thumbnails, and crawl screenshots.
