# SellerHarbor 技术架构

SellerHarbor 当前是一个本地可运行的跨境商品运营中台 MVP。系统重点不是自动发布商品，而是把商品主档、平台 Listing 状态、共享海外仓库存、真实反馈、内容生成和审核动作收口到一个可靠工作台。

## 1. 架构目标

- 首页和核心页面只依赖稳定业务接口，实验性采集能力不得影响默认可用性。
- 所有核心写操作需要可审计，关键后台任务需要超时恢复。
- 商品、反馈、生成、审核、导出这条运营闭环必须有端到端测试。
- Docker 默认栈只启动长期运行组件，避免一次性初始化容器长期显示为异常。
- 当前保留 SQLite MVP 持久化，生产高可用前迁移到 PostgreSQL 和 Redis worker。

## 2. 运行组件

```text
Browser
  |
  v
Next.js Frontend (:33001)
  |
  v
FastAPI Backend (:38081)
  |
  +-- SQLite metadata volume
  +-- MinIO object storage (:39000 / :39001)
  +-- Anthropic-compatible LLM gateway
```

Docker profiles:

- default: `backend`、`frontend`、`minio`
- `infra`: optional PostgreSQL and Redis for the next reliability phase
- `init`: optional one-shot MinIO bucket initializer
- `ops`: optional local SQLite backup loop

## 3. Backend 模块

- `app/api/routes.py`: API 路由，覆盖商品、反馈、生成、审核、概览、采集实验、健康检查。
- `app/db/repository.py`: SQLite repository 和 schema migration。
- `app/services/commerce_overview.py`: 跨境运营概览，聚合商品、平台、仓库、库存和热款信号。
- `app/services/store_registry.py`: 默认店铺、多店铺扩展槽和 storeId 数据边界。
- `app/services/business_overview.py`: 内容与评价运营概览。
- `app/services/feedback_organizer.py`: 不依赖外部模型的反馈整理能力。
- `app/agents/review_generation.py`: LangGraph / LangChain 内容生成链路。
- `app/services/readiness.py`: 生产准备度检查。
- `app/services/observability.py`: 请求指标和访问日志。
- `app/services/rate_limit.py`: 简单内存限流。
- `app/core/tenant.py`: 租户上下文和允许列表校验。

## 4. Frontend 模块

- `src/app/page.tsx`: SellerHarbor 首页。
- `src/app/(main)/dashboard/page.tsx`: 跨境运营驾驶舱。
- `src/app/(main)/products/page.tsx`: 商品主档视图。
- `src/app/(main)/feedback/page.tsx`: 真实反馈录入和整理。
- `src/app/(main)/generate/page.tsx`: 内容生成工作台。
- `src/app/(main)/review/page.tsx`: 审核与导出。
- `src/lib/api/client.ts`: API client，统一发送 `X-SellerHarbor-Tenant-ID` 和可选 API key。
- `src/lib/stores/dataStore.ts`: 前端数据加载和业务状态。

## 5. API 边界

Core APIs:

- `GET /api/commerce/overview`
- `GET /api/business/overview`
- `GET /api/stores/registry`
- `GET /api/products`
- `POST /api/products`
- `GET /api/feedback`
- `POST /api/feedback`
- `POST /api/feedback/organize`
- `POST /api/generations`
- `POST /api/generation-jobs`
- `GET /api/generation-jobs/{task_id}`
- `POST /api/generated-contents/{id}/review`
- `GET /api/audit/events`
- `GET /api/integrations/temu/status`
- `GET /api/readiness`
- `GET /api/metrics`

Hidden lab APIs:

- Open Food Facts ingestion remains available for regression and storage experiments, but it is not part of the default product flow.

## 6. 数据模型

Current MVP tables:

- `products`
- `feedbacks`
- `generation_tasks`
- `generated_contents`
- `review_records`
- `audit_events`
- `market_ingestion_runs`

Current lightweight commerce attributes are stored in `products.attributes`, including SKU, platform status, warehouse, stock, sales, rating and review counts. The next phase should migrate these fields into dedicated tables:

- `stores`
- `warehouses`
- `inventory_items`
- `inventory_movements`
- `platform_allocations`
- `platform_listings`

Store boundary:

- Tenant remains the merchant/team isolation boundary.
- Product remains tenant-level master data.
- Store represents one Temu / TikTok Shop sales account under a tenant.
- PlatformListing maps one product to one store and carries platform-specific title, status, external listing id and sync state.
- Store credentials must be encrypted and scoped per store before real multi-store sync or write-back.

## 7. 生成链路

LangGraph flow:

```text
normalize_input
  -> apply_platform_rule
  -> extract_facts
  -> policy_guard
      -> safe_alternative -> END
      -> generate_drafts
          -> evaluate_and_check_risk
              -> rewrite_drafts -> evaluate_and_check_risk -> END
              -> END
```

Important rules:

- 第一人称体验必须有真实反馈依据。
- 禁用词、平台敏感词、夸大声明和高风险请求会触发降级或拒绝。
- 高风险内容不得自动通过审核。
- 本地未配置 LLM 时，反馈整理和基础运营看板仍需可用。

## 8. 可观察性与可靠性

- 每个响应带 `X-Request-ID`。
- 多租户通过 `X-SellerHarbor-Tenant-ID` 传递。
- `/api/metrics` 暴露请求数、错误数、限流数、平均耗时和生成任务状态。
- `/api/readiness` 检查数据库、LLM、对象存储、Temu 接入、店铺注册、租户、认证、限流、任务队列、种子数据和 CORS。
- 启动时会把超时的 `pending/generating` 任务恢复为 `failed`，避免重启后永久卡住。
- Docker 默认栈使用 healthcheck 和 `depends_on: condition: service_healthy` 控制启动顺序。

## 9. 生产演进

生产化顺序：

1. SQLite 备份和恢复演练。
2. 商品、反馈、生成任务和审核记录迁移到 PostgreSQL。
3. 长任务迁移到 Redis-backed worker。
4. 加入正式用户登录、角色权限和租户管理。
5. 接入反向代理、TLS、集中日志、指标和告警。
6. 店铺、平台 Listing、共享仓库存分配和平台授权凭证迁移到结构化表。
7. 平台 CSV / API 同步加入重试、幂等、死信和审计。
