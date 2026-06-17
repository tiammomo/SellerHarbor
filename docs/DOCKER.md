# SellerHarbor Docker Components

SellerHarbor uses the SellerHarbor technical service/env prefix across Docker, runtime configuration, and API headers. Docker separates always-on local application services from optional infrastructure and operations profiles:

- `backend`: FastAPI + LangChain + LangGraph, exposed on `38081`.
- `frontend`: Next.js standalone app, exposed on `33001`.
- `minio`: S3-compatible object storage for product images and crawl screenshots.
- `minio-init`: optional one-shot bucket initializer, available through the `init` profile.
- `postgres`: optional future relational persistence component, available through the `infra` profile.
- `redis`: optional future task queue/cache component, available through the `infra` profile.
- `sqlite-backup`: optional local SQLite backup loop, available through the `ops` profile.

The current application still uses SQLite by default for metadata. MinIO is active for object assets. PostgreSQL and Redis are intentionally present but not yet wired into the application runtime; they are the migration target for the next reliability phase.

## Component Sufficiency

The current compose file is sufficient for a stable local MVP:

- Backend, frontend, and MinIO are long-running services with health checks.
- Backend waits for MinIO health before starting.
- The default stack avoids one-shot containers, so `docker compose ps` should show only running services.
- SQLite and MinIO use named volumes.
- Optional local backups are available through the `ops` profile.

It is not yet a full high-availability production stack:

- SQLite must be migrated to PostgreSQL before multi-instance backend deployment.
- FastAPI `BackgroundTasks` must be replaced by Redis-backed workers before long-running sync/crawl jobs become critical.
- Backups must be restored in drills, not only written.
- Production still needs a reverse proxy/TLS layer, centralized logs/metrics, alerting, and real user authentication.

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
- API Health: `http://localhost:38081/api/health`
- LLM Health: `http://localhost:38081/api/llm/health`
- Readiness: `http://localhost:38081/api/readiness`
- Metrics: `http://localhost:38081/api/metrics`
- MinIO API: `http://localhost:39000`
- MinIO Console: `http://localhost:39001`

The backend creates the `sellerharbor-assets` bucket lazily if it is missing. If you want to pre-create the bucket without starting the full app, run the optional initializer:

```bash
docker compose --profile init up minio-init
```

## With Optional Infrastructure Components

Start app plus PostgreSQL and Redis:

```bash
docker compose --profile infra up --build
```

Infra ports:

- PostgreSQL: `localhost:35432`
- Redis: `localhost:36379`

The `infra` profile is readiness work for the next phase. The current app still persists metadata to SQLite until repository and migration work is completed.

## With Optional Operations Components

Start the local SQLite backup loop:

```bash
docker compose --profile ops up -d sqlite-backup
```

Backup archives are written to the `sellerharbor-backups` volume as `sellerharbor-sqlite-<timestamp>.tgz`. This is a local safety net for MVP operation, not a replacement for production database backups and restore drills.

## LLM Proxy

The backend container defaults to:

```text
ANTHROPIC_BASE_URL=http://host.docker.internal:17878
ANTHROPIC_MODEL=mimo-v2.5-pro
SELLERHARBOR_LLM_CONNECT_TIMEOUT_SECONDS=5
```

On Linux, `docker-compose.yml` maps `host.docker.internal` to the host gateway through `extra_hosts`, so the container can call a local model proxy running on the host.

For production, point `ANTHROPIC_BASE_URL` at a stable Anthropic-compatible gateway instead of a developer workstation and set:

```text
SELLERHARBOR_ENV=production
SELLERHARBOR_SEED_DEMO=false
SELLERHARBOR_CORS_ALLOW_ORIGINS=https://your-frontend.example.com
SELLERHARBOR_DEFAULT_TENANT_ID=<tenant-id>
SELLERHARBOR_ALLOWED_TENANT_IDS=<tenant-a>,<tenant-b>
NEXT_PUBLIC_SELLERHARBOR_TENANT_ID=<tenant-id>
SELLERHARBOR_AUTH_REQUIRED=true
SELLERHARBOR_API_KEYS=<strong-random-key>
NEXT_PUBLIC_SELLERHARBOR_API_KEY=<same-key-for-internal-deployments>
SELLERHARBOR_RATE_LIMIT_ENABLED=true
SELLERHARBOR_RATE_LIMIT_REQUESTS_PER_MINUTE=180
SELLERHARBOR_RATE_LIMIT_GENERATION_JOBS_PER_MINUTE=12
SELLERHARBOR_GENERATION_TASK_TIMEOUT_SECONDS=600
```

`SELLERHARBOR_API_KEYS` enables a basic API-key transport gate through the `X-SellerHarbor-API-Key` header. It is useful for an internal deployment behind a trusted network or reverse proxy, but it is not a replacement for full user login and tenant-level authorization.

Tenant isolation is enforced by the `X-SellerHarbor-Tenant-ID` header. Existing local data migrates to the default tenant. In production, set `SELLERHARBOR_ALLOWED_TENANT_IDS` so unknown tenant ids are rejected before business logic runs.

## Generation Jobs

The frontend uses asynchronous generation jobs:

```bash
curl -X POST http://localhost:38081/api/generation-jobs \
  -H 'content-type: application/json' \
  -d '{"productId":"prod_x","contentType":"review_draft","platform":"taobao","tone":"natural","length":"short","persona":"third_person","count":1}'
```

Poll the returned task id:

```bash
curl http://localhost:38081/api/generation-jobs/{task_id}
```

Statuses are `pending`, `generating`, `completed`, and `failed`.

If the backend restarts while a task is `pending` or `generating`, startup recovery marks tasks older than `SELLERHARBOR_GENERATION_TASK_TIMEOUT_SECONDS` as `failed` and writes an audit event. This keeps stuck jobs visible instead of leaving them in progress forever.

## Observability

Every response includes `X-Request-ID`. Pass your ingress trace id through the same header to align proxy logs with backend logs.

Runtime counters are available at:

```bash
curl http://localhost:38081/api/metrics
```

The response includes request counts, 5xx counts, 429 counts, average latency, status distribution, and generation task status counts.

## Data Volumes

Named volumes:

- `sellerharbor-backend-data`: SQLite database for the current MVP.
- `sellerharbor-minio-data`: object storage data for product images.
- `sellerharbor-postgres-data`: optional PostgreSQL data.
- `sellerharbor-redis-data`: optional Redis append-only data.
- `sellerharbor-backups`: optional SQLite backup archives.

Reset local Docker data:

```bash
docker compose down -v
```

## Rename Migration Notes

If this machine previously ran the project under the old Docker project name, Docker may still show old volumes such as `reviewpilot_reviewpilot-backend-data` or `reviewpilot_reviewpilot-minio-data`. Do not delete them blindly if you may have created real products or imported assets before the rename.

Recommended check:

```bash
docker volume ls | grep -E 'reviewpilot|sellerharbor'
```

For the local MVP, the SQLite database lives in the backend data volume. If you need to migrate an old local database, stop the app first, back up the new database, then copy the old database into the new volume as `sellerharbor.db`:

```bash
docker compose stop backend frontend
docker run --rm \
  -v reviewpilot_reviewpilot-backend-data:/old:ro \
  -v sellerharbor_sellerharbor-backend-data:/new \
  alpine:3.20 sh -ec '
    cp /new/sellerharbor.db /new/sellerharbor.db.before-rename-migration 2>/dev/null || true
    cp /old/reviewpilot.db /new/sellerharbor.db
  '
docker compose up -d backend frontend
```

Only run that copy step when the old volume contains data you actually want to preserve. MinIO object data should be migrated through an S3 client or `mc mirror`, not by manually copying MinIO internals.

## Component Boundaries

The Docker layout intentionally keeps responsibilities separate:

- Backend owns API, LangGraph generation, product sourcing reports, and future crawler orchestration.
- Frontend owns UI and calls the backend through `NEXT_PUBLIC_API_BASE_URL`.
- PostgreSQL will own normalized product/source/snapshot metadata.
- Redis will own async job queues and short-lived crawling locks.
- MinIO/R2-compatible storage owns downloaded product images now, and will also own thumbnails and crawl screenshots later.
- `sqlite-backup` is a temporary MVP safety net until PostgreSQL owns durable metadata.

## Hidden Product Sourcing Demo

The backend still includes a hidden low-frequency ingestion path for Open Food Facts. It is kept for lab experiments and regression safety, but it is no longer part of the default SellerHarbor product flow:

```bash
curl -X POST http://localhost:38081/api/product-sourcing/ingest/open-food-facts \
  -H 'content-type: application/json' \
  -d '{"keyword":"coffee","limit":3,"force":false}'
```

Behavior:

- Uses the official Open Food Facts search API.
- Fetches at most a few products per request.
- Downloads the product image into MinIO when object storage is configured.
- Stores product name, source link, barcode/source id, MinIO-backed image URL, original image URL, object key, ingredients, labels, and nutrition metadata in the existing product pool.
- Applies a six-hour low-frequency guard for the same keyword unless `force=true`.
- The frontend no longer exposes this by default.
- Do not depend on this path for core SellerHarbor workflows.

Product images are served through the backend asset proxy:

```text
http://localhost:38081/api/assets/{object-key}
```

The bucket can stay private. If MinIO is unavailable, ingestion falls back to the original source image URL and records the storage failure in product attributes.
