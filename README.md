# ReviewPilot

ReviewPilot 是一个面向线上商家的口碑内容生成工具，帮助商家基于真实商品信息、真实服务记录和真实客户反馈，生成可审核的好评草稿、使用体验文案、推荐语和复购引导内容。

项目基于 LangChain 开发，核心目标不是伪造评价，而是把分散的商品卖点、订单场景、客户反馈和运营诉求，整理成更自然、更可信、更合规的内容草稿。

## 项目定位

- 为线上商家生成商品好评草稿、使用体验描述、推荐语、晒单引导话术和客服回访文案。
- 支持按平台、商品类目、语气、长度、客户画像和使用场景生成多版本文案。
- 在生成链路中加入事实约束、敏感词过滤、夸大宣传检测和人工审核流程。
- 帮助商家沉淀可复用的商品知识库、卖点库、真实反馈库和品牌语气库。

## 适用场景

- 商品详情页中的真实体验描述和推荐理由。
- 私域、社群、短信、邮件中的回访与评价邀请文案。
- 基于客户授权反馈整理出的评价草稿。
- 店铺运营人员批量生成不同风格、不同长度的口碑内容。
- 客服根据售后记录快速整理服务体验总结。

## 明确不做

- 不生成用于冒充真实消费者的虚假评价。
- 不支持绕过平台规则、刷评、刷单或批量灌水。
- 不编造未发生的购买、使用、效果、物流、售后或疗效事实。
- 不生成虚假的用户身份、订单截图、聊天记录或平台互动记录。

## MVP 范围

第一阶段先完成一个后端优先的生成服务：

- 商品资料录入：商品名称、类目、卖点、价格段、适用人群、禁用表达。
- 内容目标选择：好评草稿、使用体验、推荐语、评价邀请、客服回访。
- 风格参数：语气、长度、平台、是否口语化、是否带使用场景。
- LangChain 生成链：输入归一化、事实约束、文案生成、质量评估、风险检查。
- 结果管理：生成多版本、人工编辑、标记通过、导出文本。
- 基础日志：保存输入摘要、生成参数、模型响应、审核结果。

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

## Docker 组件化启动

默认只启动应用组件：

```bash
cp .env.docker.example .env
docker compose up --build
```

需要同时启动后续选品采集与图片存储基础组件：

```bash
docker compose --profile infra up --build
```

Docker 组件：

- `backend`: FastAPI + LangChain + LangGraph，端口 `38081`。
- `frontend`: Next.js standalone，端口 `33001`。
- `postgres`: 可选，后续用于商品、来源、采集快照和图片元数据。
- `redis`: 可选，后续用于异步采集任务和缓存。
- `minio`: 可选，S3 兼容对象存储，后续用于商品图、缩略图和采集截图。

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

- [产品需求文档](docs/PRD.md)
- [技术架构](docs/ARCHITECTURE.md)
- [提示词与生成策略](docs/PROMPTING.md)
- [安全与合规边界](docs/SAFETY_AND_COMPLIANCE.md)
- [开发路线图](docs/ROADMAP.md)
- [Docker 组件化运行](docs/DOCKER.md)

## 后续开发建议

优先把商品录入、反馈录入、生成、审核、复制/导出这条运营闭环打磨顺，再逐步补批量导入、异步任务、可编辑审核、导出 CSV、权限和商家租户隔离。
