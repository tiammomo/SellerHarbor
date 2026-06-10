"use client";
import { Suspense, useState, useMemo } from "react";
import { Card, Button, Select, Form, Grid, Tag, Input, Slider, Message, Spin } from "@arco-design/web-react";
import {
  IconEdit,
  IconRight,
  IconPlayArrow,
  IconRefresh,
  IconCopy,
} from "@arco-design/web-react/icon";
import { useRouter, useSearchParams } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import PageHeader from "@/components/common/PageHeader";
import ScoreBadge from "@/components/common/ScoreBadge";
import ReviewStatusTag from "@/components/common/ReviewStatusTag";
import QualityBar from "@/components/common/QualityBar";
import RiskTag from "@/components/common/RiskTag";
import {
  contentTypeLabels,
  platformLabels,
  toneLabels,
  lengthLabels,
  personaLabels,
  type ContentType,
  type Platform,
  type Tone,
  type Length,
  type Persona,
} from "@/lib/types";

const { Row, Col } = Grid;
const FormItem = Form.Item;

export default function GeneratePage() {
  return (
    <Suspense fallback={<GenerateLoading />}>
      <GenerateWorkspace />
    </Suspense>
  );
}

function GenerateLoading() {
  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="生成工作台"
        subtitle="配置生成参数，基于商品资料和真实反馈生成口碑内容"
        icon={<IconEdit />}
      />
      <Card style={{ borderRadius: 16 }}>
        <div className="flex items-center justify-center py-20">
          <Spin size={36} />
        </div>
      </Card>
    </div>
  );
}

function GenerateWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { products, feedbacks, contents, platformRules, createGeneration, updateContentReview } = useDataStore();

  const productIdFromUrl = searchParams.get("productId") || undefined;
  const feedbackIdFromUrl = searchParams.get("feedbackId") || undefined;
  const [selectedProduct, setSelectedProduct] = useState<string | undefined>(productIdFromUrl);
  const [selectedFeedback, setSelectedFeedback] = useState<string | undefined>(feedbackIdFromUrl);
  const [contentType, setContentType] = useState<ContentType>("review_draft");
  const [platform, setPlatform] = useState<Platform>("taobao");
  const [tone, setTone] = useState<Tone>("natural");
  const [length, setLength] = useState<Length>("medium");
  const [persona, setPersona] = useState<Persona>("first_person");
  const [scenario, setScenario] = useState("");
  const [count, setCount] = useState(3);
  const [generating, setGenerating] = useState(false);
  const [generatedResults, setGeneratedResults] = useState<typeof contents>([]);

  const productFeedbacks = useMemo(
    () => (selectedProduct ? feedbacks.filter((f) => f.productId === selectedProduct) : feedbacks),
    [feedbacks, selectedProduct]
  );

  const effectiveSelectedFeedback = useMemo(
    () => (selectedFeedback && productFeedbacks.some((feedback) => feedback.id === selectedFeedback) ? selectedFeedback : undefined),
    [productFeedbacks, selectedFeedback]
  );
  const selectedProductEntity = useMemo(
    () => products.find((product) => product.id === selectedProduct),
    [products, selectedProduct]
  );
  const selectedFeedbackEntity = useMemo(
    () => feedbacks.find((feedback) => feedback.id === effectiveSelectedFeedback),
    [effectiveSelectedFeedback, feedbacks]
  );
  const selectedRule = useMemo(
    () => platformRules.find((rule) => rule.platform === platform),
    [platform, platformRules]
  );
  const evidenceChecks = useMemo(
    () => buildEvidenceChecks(selectedProductEntity, selectedFeedbackEntity, selectedRule, persona, contentType),
    [contentType, persona, selectedFeedbackEntity, selectedProductEntity, selectedRule]
  );
  const scenarioOptions = selectedProductEntity?.usageScenarios.slice(0, 4) || [];

  const handleGenerate = async () => {
    if (!selectedProduct) {
      Message.warning("请先选择商品");
      return;
    }
    setGenerating(true);
    try {
      const task = await createGeneration({
        productId: selectedProduct,
        feedbackId: effectiveSelectedFeedback,
        contentType,
        platform,
        tone,
        length,
        persona,
        scenario: scenario.trim() || undefined,
        count,
      });
      setGeneratedResults(task.contents || []);
      Message.success(`已生成 ${task.contents.length} 条候选内容`);
    } catch (error) {
      Message.error(error instanceof Error ? error.message : "生成失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleReview = async (contentId: string, status: "approved" | "rejected" | "rewriting") => {
    try {
      const updated = await updateContentReview(contentId, status);
      setGeneratedResults((results) => results.map((content) => (content.id === contentId ? updated : content)));
      if (status === "approved") Message.success("已通过");
      if (status === "rejected") Message.info("已驳回");
      if (status === "rewriting") Message.info("已标记为需要重写");
    } catch (error) {
      Message.error(error instanceof Error ? error.message : "审核提交失败");
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      Message.success("已复制到剪贴板");
    } catch {
      Message.error("复制失败，请手动选择文本");
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="生成工作台"
        subtitle="配置生成参数，基于商品资料和真实反馈生成口碑内容"
        icon={<IconEdit />}
      />

      <Row gutter={16}>
        {/* Config panel */}
        <Col xs={24} lg={10}>
          <Card style={{ borderRadius: 16 }} className="mb-6">
            <h3 className="text-base font-semibold mb-4" style={{ color: "var(--text-color-1)" }}>
              生成配置
            </h3>
            <Form layout="vertical">
              <FormItem label="选择商品" required>
                <Select
                  placeholder="选择商品"
                  value={selectedProduct}
                  onChange={(value) => {
                    setSelectedProduct(value);
                    setSelectedFeedback(undefined);
                  }}
                >
                  {products.map((p) => (
                    <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
                  ))}
                </Select>
              </FormItem>

              <FormItem label="关联反馈">
                <Select
                  placeholder="选择反馈（可选）"
                  value={effectiveSelectedFeedback}
                  onChange={setSelectedFeedback}
                  allowClear
                >
                  {productFeedbacks.map((f) => (
                    <Select.Option key={f.id} value={f.id}>
                      {f.productName} - {f.sourceSummary.slice(0, 30)}...
                    </Select.Option>
                  ))}
                </Select>
              </FormItem>

              <Row gutter={12}>
                <Col span={12}>
                  <FormItem label="内容类型">
                    <Select value={contentType} onChange={setContentType}>
                      {Object.entries(contentTypeLabels).map(([key, label]) => (
                        <Select.Option key={key} value={key}>{label}</Select.Option>
                      ))}
                    </Select>
                  </FormItem>
                </Col>
                <Col span={12}>
                  <FormItem label="目标平台">
                    <Select value={platform} onChange={setPlatform}>
                      {Object.entries(platformLabels).map(([key, label]) => (
                        <Select.Option key={key} value={key}>{label}</Select.Option>
                      ))}
                    </Select>
                  </FormItem>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col span={12}>
                  <FormItem label="语气风格">
                    <Select value={tone} onChange={setTone}>
                      {Object.entries(toneLabels).map(([key, label]) => (
                        <Select.Option key={key} value={key}>{label}</Select.Option>
                      ))}
                    </Select>
                  </FormItem>
                </Col>
                <Col span={12}>
                  <FormItem label="内容长度">
                    <Select value={length} onChange={setLength}>
                      {Object.entries(lengthLabels).map(([key, label]) => (
                        <Select.Option key={key} value={key}>{label}</Select.Option>
                      ))}
                    </Select>
                  </FormItem>
                </Col>
              </Row>

              <FormItem label="人称视角">
                <Select value={persona} onChange={setPersona}>
                  {Object.entries(personaLabels).map(([key, label]) => (
                    <Select.Option key={key} value={key}>{label}</Select.Option>
                  ))}
                </Select>
              </FormItem>

              <FormItem label="使用场景">
                <Input
                  placeholder="例: 早餐豆浆、办公室喝水、送礼"
                  value={scenario}
                  onChange={setScenario}
                />
              </FormItem>
              {scenarioOptions.length > 0 && (
                <div className="flex flex-wrap gap-1 -mt-3 mb-4">
                  {scenarioOptions.map((item) => (
                    <Button key={item} size="mini" onClick={() => setScenario(item)}>
                      {item}
                    </Button>
                  ))}
                </div>
              )}

              <FormItem label={`生成数量: ${count} 条`}>
                <Slider
                  min={1}
                  max={10}
                  value={count}
                  onChange={(val) => setCount(Array.isArray(val) ? val[0] : val)}
                  showInput
                />
              </FormItem>

              <Button
                type="primary"
                long
                size="large"
                icon={generating ? <Spin size={16} /> : <IconPlayArrow />}
                onClick={handleGenerate}
                loading={generating}
                disabled={!selectedProduct}
                style={{ height: 48, fontSize: 16 }}
              >
                {generating ? "正在生成..." : "开始生成"}
              </Button>
            </Form>
          </Card>

          {selectedRule && (
            <Card style={{ borderRadius: 16 }} className="mb-6">
              <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>
                平台好评策略
              </h3>
              <div className="space-y-3">
                <StrategyRow label="目标" value={selectedRule.objective} />
                <StrategyRow label="语气" value={selectedRule.voice} />
                <div>
                  <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>结构建议</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedRule.structure.map((item) => <Tag key={item}>{item}</Tag>)}
                  </div>
                </div>
                <div>
                  <div className="text-xs mb-1" style={{ color: "var(--color-danger)" }}>规避表达</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedRule.riskTerms.slice(0, 5).map((item) => <Tag key={item} color="red">{item}</Tag>)}
                  </div>
                </div>
              </div>
            </Card>
          )}

          <Card style={{ borderRadius: 16 }} className="mb-6">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>
              证据与 Agent 路由
            </h3>
            <div className="space-y-2">
              {evidenceChecks.map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-3 rounded-xl px-3 py-2" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <span className="text-sm" style={{ color: "var(--text-color-2)" }}>{item.label}</span>
                  <Tag color={item.ok ? "green" : item.blocking ? "red" : "orange"}>
                    {item.ok ? "已满足" : item.blocking ? "会走安全替代" : "建议补充"}
                  </Tag>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
              <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>预计链路</div>
              <div className="flex flex-wrap gap-1">
                {expectedAgentRoute(evidenceChecks).map((item) => (
                  <Tag key={item} color={item === "safe_alternative" ? "orange" : item === "rewrite_drafts" ? "gold" : "blue"}>
                    {item}
                  </Tag>
                ))}
              </div>
            </div>
          </Card>

          {/* Selected product preview */}
          {selectedProduct && (() => {
            const product = selectedProductEntity;
            if (!product) return null;
            return (
              <Card style={{ borderRadius: 16 }} className="mb-6 animate-fade-in">
                <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>
                  商品资料
                </h3>
                <div className="text-base font-medium mb-2" style={{ color: "var(--text-color-1)" }}>
                  {product.name}
                </div>
                <Tag color="blue" className="mb-3">{product.category}</Tag>
                <div className="mb-3">
                  <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>卖点</div>
                  <div className="flex flex-wrap gap-1">
                    {product.sellingPoints.map((sp) => (
                      <Tag key={sp} style={{ borderRadius: 8, fontSize: 12 }}>{sp}</Tag>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-xs mb-1" style={{ color: "var(--color-danger)" }}>禁用词</div>
                  <div className="flex flex-wrap gap-1">
                    {product.forbiddenClaims.map((fc) => (
                      <Tag key={fc} color="red" style={{ borderRadius: 8, fontSize: 12 }}>{fc}</Tag>
                    ))}
                  </div>
                </div>
                {selectedFeedbackEntity && (
                  <div className="mt-3 pt-3 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                    <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>关联反馈事实</div>
                    <div className="flex flex-wrap gap-1">
                      {selectedFeedbackEntity.confirmedFacts.map((fact) => (
                        <Tag key={fact} color="green" style={{ borderRadius: 8, fontSize: 12 }}>{fact}</Tag>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            );
          })()}
        </Col>

        {/* Results panel */}
        <Col xs={24} lg={14}>
          {generatedResults.length === 0 && !generating ? (
            <Card style={{ borderRadius: 16 }}>
              <div className="flex flex-col items-center justify-center py-20">
                <div className="text-6xl mb-4">✨</div>
                <h3 className="text-lg font-medium mb-2" style={{ color: "var(--text-color-2)" }}>
                  配置参数后开始生成
                </h3>
                <p className="text-sm" style={{ color: "var(--text-color-3)" }}>
                  生成的内容将显示在这里，支持逐条审核和编辑
                </p>
              </div>
            </Card>
          ) : generating ? (
            <Card style={{ borderRadius: 16 }}>
              <div className="flex flex-col items-center justify-center py-20">
                <Spin size={48} />
                <p className="mt-4 text-sm" style={{ color: "var(--text-color-3)" }}>
                  正在基于商品资料和客户反馈生成内容...
                </p>
              </div>
            </Card>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold" style={{ color: "var(--text-color-1)" }}>
                  生成结果 ({generatedResults.length} 条)
                </h3>
                <div className="flex gap-2">
                  <Button icon={<IconRefresh />} onClick={handleGenerate}>重新生成</Button>
                  <Button type="primary" onClick={() => router.push("/review")}>
                    去审核 <IconRight />
                  </Button>
                </div>
              </div>

              {generatedResults.map((content, index) => (
                <Card
                  key={content.id}
                  className="hover-lift animate-fade-in"
                  style={{ borderRadius: 16, animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>
                        候选 #{index + 1}
                      </span>
                      <ScoreBadge score={content.score} />
                    </div>
                    <RiskTag flags={content.riskFlags} />
                  </div>

                  <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-color-2)" }}>
                    {content.text}
                  </p>

                  {/* Quality report */}
                  <div className="p-4 rounded-xl mb-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <div className="text-xs font-medium mb-3" style={{ color: "var(--text-color-2)" }}>质量报告</div>
                    <div className="space-y-2">
                      <QualityBar label="自然度" value={content.qualityReport.naturalness} />
                      <QualityBar label="具体度" value={content.qualityReport.specificity} />
                      <QualityBar label="事实一致" value={content.qualityReport.factConsistency} />
                      <QualityBar label="平台适配" value={content.qualityReport.platformFit} />
                      <QualityBar label="重复风险" value={100 - content.qualityReport.repetitionRisk} />
                      <QualityBar label="夸大风险" value={100 - content.qualityReport.exaggerationRisk} />
                    </div>
                  </div>

                  {/* Source trace */}
                  <div>
                    <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>Agent 链路与来源依据</div>
                    <div className="flex flex-wrap gap-1">
                      {content.sourceTrace.map((trace) => (
                        <Tag
                          key={trace}
                          color={trace.startsWith("agent.node") ? "blue" : undefined}
                          style={{ borderRadius: 8, fontSize: 11 }}
                        >
                          {trace}
                        </Tag>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4 pt-3 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                    <ReviewStatusTag status={content.reviewStatus} />
                    <div className="flex-1" />
                    <Button size="small" icon={<IconCopy />} onClick={() => handleCopy(content.text)}>
                      复制
                    </Button>
                    {content.reviewStatus === "pending" && (
                      <>
                        <Button type="primary" size="small" onClick={() => handleReview(content.id, "approved")}>
                          通过
                        </Button>
                        <Button status="danger" size="small" onClick={() => handleReview(content.id, "rejected")}>
                          驳回
                        </Button>
                        <Button size="small" icon={<IconRefresh />} onClick={() => handleReview(content.id, "rewriting")}>
                          标记重写
                        </Button>
                      </>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </Col>
      </Row>
    </div>
  );
}

function StrategyRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>{label}</div>
      <div className="text-sm leading-relaxed" style={{ color: "var(--text-color-2)" }}>{value}</div>
    </div>
  );
}

function buildEvidenceChecks(
  product: ReturnType<typeof useDataStore.getState>["products"][number] | undefined,
  feedback: ReturnType<typeof useDataStore.getState>["feedbacks"][number] | undefined,
  rule: ReturnType<typeof useDataStore.getState>["platformRules"][number] | undefined,
  persona: Persona,
  contentType: ContentType
) {
  const isExperienceContent = ["review_draft", "experience_copy", "recommendation"].includes(contentType);
  const needsFeedback = Boolean(rule?.requireExperienceEvidence && isExperienceContent);
  const merchantVoiceRisk = Boolean(rule?.merchantVoiceReviewRisk && persona === "merchant" && isExperienceContent);
  return [
    { label: "商品卖点不少于 2 条", ok: Boolean(product && product.sellingPoints.length >= 2), blocking: false },
    { label: "具备使用场景", ok: Boolean(product && product.usageScenarios.length > 0), blocking: false },
    { label: "配置禁用表达", ok: Boolean(product && product.forbiddenClaims.length > 0), blocking: false },
    { label: "平台要求真实体验依据", ok: !needsFeedback || Boolean(feedback), blocking: needsFeedback && !feedback && persona === "first_person" },
    { label: "人称与平台合规", ok: !merchantVoiceRisk, blocking: merchantVoiceRisk },
  ];
}

function expectedAgentRoute(checks: Array<{ blocking: boolean; ok: boolean }>) {
  if (checks.some((item) => item.blocking)) {
    return ["policy_guard", "safe_alternative"];
  }
  if (checks.some((item) => !item.ok)) {
    return ["policy_guard", "generate_drafts", "evaluate_and_check_risk", "rewrite_drafts?"];
  }
  return ["policy_guard", "generate_drafts", "evaluate_and_check_risk"];
}
