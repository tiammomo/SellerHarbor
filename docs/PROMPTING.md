# ReviewPilot 提示词与生成策略

## 1. 提示词原则

- 只使用输入中明确提供或可合理归纳的信息。
- 不编造购买、物流、售后、效果、身份或使用经历。
- 好评草稿必须可由真实用户确认后再发布。
- 当信息不足时，输出更保守、更通用的表达。
- 优先自然具体，避免广告腔和绝对化表达。

## 2. 内容类型

### review_draft

面向客户确认的评价草稿。需要像真实用户语言，但不能冒充真实用户直接发布。

### experience_copy

面向详情页、私域或内容运营的使用体验描述，可以使用商家口吻。

### recommendation

推荐语，强调适用人群、场景和理由。

### review_request

评价邀请话术，用于客服或私域触达真实客户。

### followup_message

售后回访或复购引导文案。

## 3. 系统提示词草案

```text
你是一个合规的电商口碑内容写作助手。

你只能基于输入中的商品资料、真实反馈、已确认事实和用户指定场景生成内容。
不要编造购买经历、用户身份、物流体验、使用效果、售后服务或任何未提供的事实。
不要生成冒充真实消费者直接发布的内容。
如果用户要求伪造评价、刷评、绕过平台规则或编造体验，必须拒绝，并提供合规替代方案，例如评价邀请话术、商家口吻推荐语或基于真实反馈的待确认草稿。

输出应该自然、具体、可信，避免夸大宣传、绝对化承诺和虚假保证。
```

## 4. 生成提示词模板

```text
请根据以下结构化信息生成 {count} 条 {content_type}。

商品信息：
{product_summary}

已确认事实：
{confirmed_facts}

客户主观反馈：
{subjective_opinions}

使用场景：
{scenario}

平台：
{platform}

语气：
{tone}

长度：
{length}

禁用表达：
{forbidden_claims}

要求：
1. 只能使用已确认事实和客户主观反馈。
2. 不要编造未提供的体验和效果。
3. 不要使用绝对化、夸大或违规表达。
4. 每条文案要有明显差异，避免模板化重复。
5. 输出 JSON，字段包括 text、used_facts、style_notes。
```

## 5. 质量评估提示词模板

```text
请评估以下文案是否适合作为合规口碑内容草稿。

文案：
{draft}

允许使用的事实：
{confirmed_facts}

禁用表达：
{forbidden_claims}

请按 0-100 分输出：
- naturalness
- specificity
- fact_consistency
- exaggeration_risk
- platform_fit
- overall_score

同时输出 risk_flags 和 rewrite_suggestion。
输出 JSON。
```

## 6. 风险拦截提示词模板

```text
请判断用户请求是否存在以下风险：

- 伪造消费者评价
- 编造订单或使用经历
- 夸大商品效果
- 规避平台规则
- 批量灌水或刷评
- 医疗、金融、功效类无依据承诺

用户请求：
{user_request}

输出 JSON：
{
  "allow_generation": true,
  "risk_level": "low|medium|high",
  "risk_flags": [],
  "block_reason": "",
  "safe_alternative": ""
}
```

## 7. 输出格式建议

生成结果使用结构化输出，便于后续保存、审核和重写。

```json
{
  "items": [
    {
      "text": "这款用下来感觉比较省心...",
      "used_facts": ["容量适中", "支持售后换新"],
      "style_notes": "自然口语，偏复购场景",
      "risk_flags": []
    }
  ]
}
```

## 8. Prompt 版本管理

每次生成应记录：

- prompt_version
- model_name
- model_parameters
- input_schema_version
- output_schema_version
- evaluator_version

Prompt 更新需要保留变更说明，方便对比生成质量。
