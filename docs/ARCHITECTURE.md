# ReviewPilot 技术架构

## 1. 架构目标

- 以 LangChain 为核心编排层，把输入整理、生成、评估、风控和重写拆成可观察的链路。
- 生成结果必须可追溯到商品资料、真实反馈和用户配置。
- 优先实现简单可靠的同步 API，当前生成链路已用 LangGraph 编排，后续再扩展为异步任务。
- 每个节点都输出结构化结果，便于调试、评估和人工审核。

## 2. 高层模块

```text
Client / Admin UI
        |
        v
FastAPI Backend
        |
        +-- Product Service
        +-- Feedback Service
        +-- Generation Service
        +-- Review Service
        |
        v
LangGraph / LangChain Orchestration
        |
        +-- Input Normalizer
        +-- Fact Extractor
        +-- Policy Guard
        +-- Draft Generator
        +-- Quality Evaluator
        +-- Risk Checker
        +-- Rewrite Chain
        +-- Safe Alternative Builder
        |
        v
LLM Provider / Embedding Provider / Vector Store
```

当前 MVP 的 LangGraph 编排是条件图：

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

`safe_alternative` 用于不可安全生成的请求，例如小红书第一人称体验但缺少真实反馈依据。`rewrite_drafts` 用于第一次生成后出现禁用词、平台敏感词、高重复风险、高夸大风险或低质量分的候选内容，当前最多自动重写一次。

模型调用由 LangChain Runnable 承载：

```text
ChatPromptTemplate -> LocalAnthropic Runnable -> JSON parser
```

`LocalAnthropic Runnable` 调用本地 Claude Code 配置里的 Anthropic-compatible `/v1/messages`，默认模型为 `mimo-v2.5-pro`。这样 LangGraph 负责节点和分支，LangChain 负责 prompt/message/model/parser 链路。

## 3. LangChain 链路设计

### 3.1 Input Normalizer

把用户输入、商品资料和反馈内容整理成统一 schema。

输入：

- Product
- Feedback
- GenerationConfig

输出：

- NormalizedGenerationInput

职责：

- 去掉明显无关内容。
- 标记事实、观点和商家诉求。
- 补齐默认参数。
- 对平台、语气和长度做标准化。

### 3.2 Fact Extractor

从商品资料和真实反馈中提取允许使用的事实。

输出字段：

- confirmed_facts
- allowed_subjective_points
- forbidden_or_uncertain_points
- missing_information

原则：

- 没有依据的信息不能作为事实写入。
- 不确定信息只能作为待确认项，不能进入最终生成。
- 医疗、功效、收益、绝对化表达需要单独标记。

### 3.3 Policy Guard

在生成前检查输入是否存在明显违规意图。

拦截示例：

- 要求伪装成真实消费者。
- 要求编造订单、体验、效果或身份。
- 要求绕过平台审核。
- 要求生成大量重复灌水内容。

输出：

- allow_generation
- block_reason
- safe_alternative

### 3.4 Draft Generator

根据结构化输入生成候选文案。

需要支持：

- 多版本生成。
- 风格控制。
- 平台适配。
- 长度控制。
- 禁用词约束。
- 事实引用约束。

输出：

- drafts
- generation_notes

### 3.5 Quality Evaluator

对候选文案进行打分，输出结构化质量报告。

评分维度：

- naturalness
- specificity
- fact_consistency
- platform_fit
- repetition_risk
- exaggeration_risk
- overall_score

### 3.6 Risk Checker

做更严格的风险检查。

风险类型：

- fabricated_experience
- unsupported_claim
- prohibited_claim
- medical_or_financial_claim
- platform_policy_risk
- spam_pattern
- impersonation_risk

### 3.7 Rewrite Chain

当内容质量不足或存在轻微风险时自动重写。

重写策略：

- 删除无依据事实。
- 降低夸大语气。
- 增加真实场景细节。
- 去除广告腔。
- 改为评价邀请或商家口吻文案。

## 4. 后端 API 草案

### POST /api/products

创建商品资料。

### GET /api/products

查询商品列表。

### POST /api/feedback

录入真实反馈或服务记录摘要。

### POST /api/generations

创建生成任务。

请求核心字段：

```json
{
  "productId": "prod_123",
  "feedbackId": "fb_123",
  "contentType": "review_draft",
  "platform": "taobao",
  "tone": "natural",
  "length": "medium",
  "scenario": "repeat_purchase",
  "count": 5
}
```

响应核心字段：

```json
{
  "id": "task_123",
  "productId": "prod_123",
  "status": "completed",
  "contents": [
    {
      "id": "gen_123",
      "taskId": "task_123",
      "text": "这次回购主要是因为...",
      "score": 86,
      "riskFlags": [],
      "sourceTrace": ["product.selling_points", "feedback.subjective_opinions"],
      "reviewStatus": "pending"
    }
  ]
}
```

### POST /api/generations/{id}/review

提交人工审核结果。

## 5. 数据存储

### PostgreSQL

保存结构化业务数据：

- products
- feedback
- generation_tasks
- generated_contents
- review_records
- prompt_versions

### Vector Store

保存可检索知识：

- 品牌语气样例
- 商品常用卖点
- 已通过的高质量文案
- 平台规则摘要

MVP 可以先用 PostgreSQL + pgvector，后续视规模替换为专门向量数据库。

### Redis

用于：

- 短期缓存
- 异步任务状态
- 幂等请求锁

## 6. 可观察性

建议接入 LangSmith 追踪：

- 每个链路节点的输入输出。
- Prompt 版本。
- 模型参数。
- Token 消耗。
- 延迟。
- 质量评分。
- 风险标记。

同时在业务数据库保存精简审计日志，避免只依赖外部调试平台。

## 7. 目录结构建议

```text
ReviewPilot/
  app/
    api/
    chains/
    core/
    models/
    repositories/
    schemas/
    services/
  docs/
  tests/
  README.md
  pyproject.toml
  .env.example
```

## 8. 后续演进

- 从单条同步生成升级到异步批量生成。
- 用 LangGraph 编排生成、检查、重写、人工审核。
- 引入 RAG 检索品牌语气、平台规范和商品知识。
- 增加 A/B 测试和人工反馈学习。
- 增加多租户权限、团队审核和操作日志。
