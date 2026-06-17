# SellerHarbor 文档地图

这组文档用于维护 SellerHarbor 的产品定位、技术边界、运行方式和后续路线。

## 产品与路线

- [产品需求文档](PRD.md)：业务背景、用户角色、核心功能、数据对象和成功指标。
- [长期能力规划](CAPABILITY_PLAN.md)：商品主档、平台 Listing、海外仓、热款追踪和高可用方向。
- [开发路线图](ROADMAP.md)：当前基线、分阶段交付计划和延后能力。

## 技术与运行

- [技术架构](ARCHITECTURE.md)：前后端、服务模块、API 边界、数据模型、生成链路和可靠性设计。
- [Docker 组件化运行](DOCKER.md)：本地启动、可选 infra/ops/init profile、数据卷和改名迁移说明。

## 内容安全

- [提示词与生成策略](PROMPTING.md)：生成原则、内容类型、提示词模板和 Prompt 版本管理。
- [安全与合规边界](SAFETY_AND_COMPLIANCE.md)：允许内容、禁止内容、事实约束、风险分级和审核要求。

## 当前维护口径

- SellerHarbor 是跨境卖家的商品运营港，不是刷评工具，也不是完整 ERP。
- 默认产品主线是商品、平台、仓库、库存、反馈、热款和人工审核。
- Open Food Facts 等公开采集能力只保留为隐藏实验能力。
- 本地 MVP 使用 SQLite；生产高可用前需要迁移到 PostgreSQL 和 Redis worker。
- 所有核心能力必须持续通过后端测试、前端 lint/build、依赖审计和 Docker healthcheck。
