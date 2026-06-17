# SellerHarbor

SellerHarbor 是一个面向 Temu、TikTok Shop 等跨境平台商家的跨境卖家商品运营港，帮助个人卖家和小团队把商品主数据、平台上架资料、海外仓库存、评价反馈和热款信号收口到同一个工作台。

当前技术仓库、Docker 服务名、环境变量和 API Header 已统一采用 SellerHarbor 命名。

项目基于 FastAPI、Next.js 和 LangChain 开发。核心目标不是伪造评价，也不是替代平台后台，而是把跨境卖家分散在不同平台、仓库和素材表里的商品运营数据整理成可追踪、可审核、可行动的运营闭环。

## 项目定位

- 作为跨境商品主数据中心，统一管理 SKU、变体、卖点、图片、平台字段和上架准备度。
- 面向 Temu、TikTok Shop 等平台整理商品 Listing、详情页素材、评价邀请和客服回访话术。
- 管理多平台共享海外仓库存，追踪可用库存、安全库存、占用库存和低库存预警。
- 追踪好评、评分、销量、热款和潜力款，辅助判断补货、扩平台和素材优化优先级。
- 保留合规内容生成与人工审核能力，避免虚构评价、夸大宣传和平台违规表达。

## 适用场景

- 个人卖家同时运营 Temu、TikTok Shop 等平台，需要统一维护商品资料和上架状态。
- 多个平台共享同一批海外仓，需要明确 SKU 在不同仓库、不同平台的库存分配。
- 需要快速发现热款、潜力款、低库存款、差评风险款和上架资料缺失商品。
- 需要把真实评价、客服反馈和商品卖点整理为详情页口碑素材、邀评话术和客服回访内容。

## 明确不做

- 不生成用于冒充真实消费者的虚假评价。
- 不支持绕过平台规则、刷评、刷单或批量灌水。
- 不编造未发生的购买、使用、效果、物流、售后或疗效事实。
- 不生成虚假的用户身份、订单截图、聊天记录或平台互动记录。
- 不在当前阶段替代完整 ERP、财务系统或平台官方订单履约后台。
- 不自动发布商品或自动调整平台库存，第一阶段只做集中管理、预警和导出准备。

## MVP 范围

第一阶段从“内容生成工具”升级为“跨境商品运营中台 MVP”：

- 商品主档：商品名称、类目、SKU、平台、仓库、库存、卖点、禁用表达和上架状态。
- 跨境运营概览：Temu / TikTok Shop Listing 就绪率、海外仓库存健康率、低库存预警和热款追踪。
- 仓储轻管理：先基于商品属性管理仓库、可用库存、占用库存和安全库存，后续再迁移到独立库存表。
- 内容与评价模块：继续支持真实反馈整理、评价邀请、客服回访、推荐语、详情页口碑素材生成和审核。
- 观测与可靠性：保留健康检查、请求 ID、指标、租户隔离、限流、超时任务恢复和端到端测试。

## 当前实现

- Frontend：Next.js + React + Arco Design。
- Backend：Python + FastAPI + LangChain + LangGraph，默认使用 SQLite 本地数据库，接口字段与前端 TypeScript 类型保持 camelCase 对齐。
- LLM：默认读取本机 Claude Code 配置，当前目标模型为 `mimo-v2.5-pro`，本地代理地址可通过 `ANTHROPIC_BASE_URL` 配置。
- Python 依赖使用 `uv` 管理，下载缓存与托管 Python 版本在用户级目录复用，后续其他 Python 项目可以沿用同一套缓存。

## 本地启动

启动后端：

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 38081 --reload
```

启动前端：

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

- Frontend: `http://localhost:33001`
- Backend: `http://localhost:38081`
- Health: `http://localhost:38081/healthz`
- API Health: `http://localhost:38081/api/health`
- LLM Health: `http://localhost:38081/api/llm/health`
- Readiness: `http://localhost:38081/api/readiness`
- Metrics: `http://localhost:38081/api/metrics`
- Business Overview: `http://localhost:38081/api/business/overview`
- Commerce Overview: `http://localhost:38081/api/commerce/overview`

生产环境建议显式设置：

- `SELLERHARBOR_ENV=production`
- `SELLERHARBOR_SEED_DEMO=false`
- `SELLERHARBOR_CORS_ALLOW_ORIGINS=https://your-frontend.example.com`
- `SELLERHARBOR_DEFAULT_TENANT_ID=<tenant-id>`
- `SELLERHARBOR_ALLOWED_TENANT_IDS=<tenant-a>,<tenant-b>`
- `NEXT_PUBLIC_SELLERHARBOR_TENANT_ID=<tenant-id>`
- `SELLERHARBOR_AUTH_REQUIRED=true`
- `SELLERHARBOR_API_KEYS=<strong-random-key>`
- `NEXT_PUBLIC_SELLERHARBOR_API_KEY=<same-key-for-internal-deployments>`
- `SELLERHARBOR_RATE_LIMIT_ENABLED=true`
- `SELLERHARBOR_RATE_LIMIT_REQUESTS_PER_MINUTE=180`
- `SELLERHARBOR_RATE_LIMIT_GENERATION_JOBS_PER_MINUTE=12`
- `SELLERHARBOR_GENERATION_TASK_TIMEOUT_SECONDS=600`
- `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL`
- `SELLERHARBOR_LLM_CONNECT_TIMEOUT_SECONDS=5`

生成接口支持同步和异步两种模式：

- `POST /api/generations`：同步生成，适合本地调试。
- `POST /api/generation-jobs`：异步提交生成任务，返回 `202` 和任务 ID。
- `GET /api/generation-jobs/{task_id}`：轮询 `pending` / `generating` / `completed` / `failed` 状态。
- `POST /api/feedback/organize`：把原始客户反馈整理成摘要、已确认事实、主观感受、风险标记和推荐用途，不依赖外部模型。

关键写操作会记录审计事件，可通过 `GET /api/audit/events` 查看最近事件。

运行时观测：

- 所有 HTTP 响应会带 `X-Request-ID`，可通过同名请求头传入外部 trace id。
- 所有业务请求会按 `X-SellerHarbor-Tenant-ID` 做租户隔离；未传时使用 `SELLERHARBOR_DEFAULT_TENANT_ID`。
- `/api/metrics` 提供请求总数、错误数、限流数、平均耗时和生成任务状态分布。
- 启动时会把超过 `SELLERHARBOR_GENERATION_TASK_TIMEOUT_SECONDS` 的 `pending/generating` 任务标记为 `failed`，避免进程重启后任务永久卡住。

端到端验证：

```bash
cd backend
uv run python -m unittest discover -s tests

cd ../frontend
npm run audit
npm run lint
npm run build
```

后端测试覆盖整理链路：创建商品、整理原始反馈、保存反馈、更新业务概览、生成候选内容、审核通过并进入可导出素材池；同时覆盖禁用词和高风险声明降级路径。

## Docker 组件化启动

默认启动应用组件和 MinIO 对象存储：

```bash
cp .env.docker.example .env
docker compose up --build
```

需要同时启动 PostgreSQL / Redis 等后续基础组件：

```bash
docker compose --profile infra up --build
```

Docker 组件：

- `backend`: FastAPI + LangChain + LangGraph，端口 `38081`。
- `frontend`: Next.js standalone，端口 `33001`。
- `minio`: S3 兼容对象存储，用于保存自动采集的商品图片，API 端口 `39000`，控制台端口 `39001`。
- `minio-init`: 可选一次性建桶组件，通过 `init` profile 手动运行，避免默认栈出现退出容器。
- `postgres`: 可选，通过 `infra` profile 启动，后续用于商品、来源、采集快照和图片元数据。
- `redis`: 可选，通过 `infra` profile 启动，后续用于异步采集任务和缓存。
- `sqlite-backup`: 可选，通过 `ops` profile 启动，为当前 SQLite MVP 提供本地备份安全网。

当前 Docker 默认栈足够支撑本地 MVP：前端、后端和 MinIO 都是长期运行组件并带健康检查；完整高可用生产化仍需要把 SQLite 迁移到 PostgreSQL、把长任务迁移到 Redis worker，并补齐备份恢复演练、反向代理/TLS、集中日志、告警和正式登录权限。

更多说明见 [Docker Components](docs/DOCKER.md)。

## 推荐技术栈

- Python 3.13+
- FastAPI：提供生成 API 和管理接口。
- Pydantic：维护前后端一致的数据 schema。
- SQLite：MVP 本地持久化，后续可迁移 PostgreSQL。
- LangChain：编排提示词、模型调用、结构化输出和工具链。
- LangGraph：编排生成、规则、事实提取、风控和评估节点。
- PostgreSQL：保存商品、任务、生成结果和审核记录。
- Redis：异步任务队列和短期缓存。
- LangSmith：调试、追踪和评估生成链路。

## 文档

- [文档地图](docs/README.md)
- [产品需求文档](docs/PRD.md)
- [技术架构](docs/ARCHITECTURE.md)
- [提示词与生成策略](docs/PROMPTING.md)
- [安全与合规边界](docs/SAFETY_AND_COMPLIANCE.md)
- [开发路线图](docs/ROADMAP.md)
- [长期能力规划](docs/CAPABILITY_PLAN.md)
- [Docker 组件化运行](docs/DOCKER.md)

## 后续开发建议

优先把商品录入、反馈录入、生成、审核、复制/导出这条运营闭环打磨顺，再逐步补批量导入、异步任务、可编辑审核、导出 CSV、权限和商家租户隔离。
