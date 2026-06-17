"use client";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { Card, Button, Tag, Input, Grid, Modal, Form, Select, Message } from "@arco-design/web-react";
import {
  IconPlus,
  IconSearch,
  IconApps,
  IconRight,
} from "@arco-design/web-react/icon";
import { useRouter } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import ScoreBadge from "@/components/common/ScoreBadge";
import {
  platformLabels,
  type Feedback,
  type GeneratedContent,
  type GenerationTask,
  type Platform,
  type Product,
  type ProductMarketSource,
  type ProductOpportunityReport,
  type ProductResearchProvider,
  type ProductVisual,
} from "@/lib/types";

const { Row, Col } = Grid;
const FormItem = Form.Item;

type OpportunityFilter = "all" | "high" | "watch" | "needs_evidence";
type SortKey = "opportunity" | "feedback" | "score" | "recent";

type ProductInsight = {
  product: Product;
  feedbackCount: number;
  generationCount: number;
  approvedCount: number;
  riskCount: number;
  avgScore: number;
  completeness: number;
  opportunityScore: number;
  level: "high" | "watch" | "needs_evidence";
  recommendedPlatforms: Platform[];
  gaps: string[];
  nextAction: string;
  sourcingConfidence: number;
  recommendedProviderIds: string[];
  providerNames: string[];
  validationMissing: number;
  visual: ProductVisual;
  marketSources: ProductMarketSource[];
  collectionPlan: ProductOpportunityReport["collectionPlan"];
  report?: ProductOpportunityReport;
};

export default function ProductsPage() {
  const router = useRouter();
  const {
    products,
    feedbacks,
    tasks,
    contents,
    productResearchProviders,
    productOpportunityReports,
    createProduct,
  } = useDataStore();
  const [productForm] = Form.useForm();
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [platformFilter, setPlatformFilter] = useState<Platform | undefined>();
  const [opportunityFilter, setOpportunityFilter] = useState<OpportunityFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("opportunity");
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<ProductResearchProvider | null>(null);
  const [addVisible, setAddVisible] = useState(false);

  const categories = useMemo(() => [...new Set(products.map((p) => p.category))], [products]);
  const providerById = useMemo(
    () => new Map(productResearchProviders.map((provider) => [provider.id, provider])),
    [productResearchProviders]
  );
  const reportByProductId = useMemo(
    () => new Map(productOpportunityReports.map((report) => [report.productId, report])),
    [productOpportunityReports]
  );

  const insights = useMemo(
    () => products.map((product) => buildProductInsight(product, feedbacks, tasks, contents, reportByProductId.get(product.id), providerById)),
    [contents, feedbacks, products, providerById, reportByProductId, tasks]
  );

  const summary = useMemo(
    () => ({
      total: insights.length,
      high: insights.filter((item) => item.level === "high").length,
      evidenceReady: insights.filter((item) => item.feedbackCount > 0).length,
      riskNeedsReview: insights.filter((item) => item.riskCount > 0).length,
      externallyScored: insights.filter((item) => item.report).length,
    }),
    [insights]
  );

  const filteredInsights = useMemo(() => {
    return [...insights]
      .filter((item) => {
        const product = item.product;
        const matchSearch = !search || product.name.includes(search) || product.category.includes(search);
        const matchCategory = !selectedCategory || product.category === selectedCategory;
        const matchPlatform = !platformFilter || item.recommendedPlatforms.includes(platformFilter);
        const matchOpportunity = opportunityFilter === "all" || item.level === opportunityFilter;
        return matchSearch && matchCategory && matchPlatform && matchOpportunity;
      })
      .sort((a, b) => {
        if (sortKey === "feedback") return b.feedbackCount - a.feedbackCount;
        if (sortKey === "score") return b.avgScore - a.avgScore;
        if (sortKey === "recent") return new Date(b.product.updatedAt).getTime() - new Date(a.product.updatedAt).getTime();
        return b.opportunityScore - a.opportunityScore;
      });
  }, [insights, opportunityFilter, platformFilter, search, selectedCategory, sortKey]);

  const selectedInsight = selectedProduct ? insights.find((item) => item.product.id === selectedProduct.id) : undefined;

  const openDetail = (product: Product) => {
    setSelectedProduct(product);
    setDetailVisible(true);
  };

  const handleCreateProduct = async () => {
    try {
      const values = await productForm.validate();
      await createProduct({
        name: values.name,
        category: values.category,
        attributes: buildAttributes(values),
        sellingPoints: splitLines(values.sellingPoints),
        targetAudiences: splitComma(values.targetAudiences),
        usageScenarios: splitComma(values.usageScenarios),
        forbiddenClaims: splitComma(values.forbiddenClaims),
      });
      Message.success("商品主档已保存");
      productForm.resetFields();
      setAddVisible(false);
    } catch (error) {
      if (error instanceof Error) Message.error(error.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="商品主档"
        subtitle="统一维护 SKU、平台 Listing、海外仓库存、卖点和素材准备度"
        icon={<IconApps />}
        extra={
          <div className="flex flex-wrap gap-2">
            <Button type="primary" icon={<IconPlus />} onClick={() => setAddVisible(true)}>
              新增商品主档
            </Button>
          </div>
        }
      />

      <Row gutter={16} className="mb-6">
        <SummaryCard label="商品主档" value={summary.total} tone="blue" />
        <SummaryCard label="重点商品" value={summary.high} tone="green" />
        <SummaryCard label="有反馈依据" value={summary.evidenceReady} tone="cyan" />
        <SummaryCard label="待补资料" value={summary.riskNeedsReview} tone="orange" />
      </Row>

      <Card className="mb-6" style={{ borderRadius: 16 }}>
        <div className="flex flex-wrap items-center gap-4">
          <Input
            prefix={<IconSearch style={{ color: "var(--text-color-4)" }} />}
            placeholder="搜索商品名称或类目..."
            value={search}
            onChange={setSearch}
            style={{ width: 260 }}
          />
          <Select placeholder="全部类目" value={selectedCategory} onChange={setSelectedCategory} allowClear style={{ width: 150 }}>
            {categories.map((cat) => (
              <Select.Option key={cat} value={cat}>{cat}</Select.Option>
            ))}
          </Select>
          <Select placeholder="平台适配" value={platformFilter} onChange={setPlatformFilter} allowClear style={{ width: 150 }}>
            {Object.entries(platformLabels).map(([key, label]) => (
              <Select.Option key={key} value={key}>{label}</Select.Option>
            ))}
          </Select>
          <Select value={opportunityFilter} onChange={setOpportunityFilter} style={{ width: 150 }}>
            <Select.Option value="all">全部机会</Select.Option>
            <Select.Option value="high">高机会</Select.Option>
            <Select.Option value="watch">可观察</Select.Option>
            <Select.Option value="needs_evidence">待补证据</Select.Option>
          </Select>
          <Select value={sortKey} onChange={setSortKey} style={{ width: 150 }}>
            <Select.Option value="opportunity">机会分排序</Select.Option>
            <Select.Option value="feedback">反馈数排序</Select.Option>
            <Select.Option value="score">质量分排序</Select.Option>
            <Select.Option value="recent">最近更新</Select.Option>
          </Select>
          <div className="flex-1" />
          <span className="text-sm" style={{ color: "var(--text-color-3)" }}>
            共 {filteredInsights.length} 个商品
          </span>
        </div>
      </Card>

      {filteredInsights.length === 0 ? (
        <EmptyState
          icon="📦"
          title="暂无匹配商品"
          description="补充商品资料、反馈依据后即可开始生成口碑内容"
          actionText="新增商品"
          onAction={() => setAddVisible(true)}
        />
      ) : (
        <Row gutter={16}>
          {filteredInsights.map((item, index) => (
            <Col key={item.product.id} xs={24} sm={12} lg={8}>
              <Card
                className="mb-4 hover-lift animate-fade-in cursor-pointer"
                style={{ borderRadius: 16, animationDelay: `${index * 50}ms` }}
                onClick={() => openDetail(item.product)}
              >
                <ProductImage visual={item.visual} name={item.product.name} compact />
                <div className="flex items-start justify-between mb-3">
                  <div className="min-w-0">
                    <h3 className="text-base font-semibold m-0 mb-1 truncate" style={{ color: "var(--text-color-1)" }}>
                      {item.product.name}
                    </h3>
                    <div className="flex flex-wrap gap-1">
                      <Tag color="blue">{item.product.category}</Tag>
                      <OpportunityTag level={item.level} />
                    </div>
                  </div>
                  <ScoreBadge score={item.opportunityScore} />
                </div>

                <div className="grid grid-cols-3 gap-2 mb-4">
                  <MiniMetric label="机会分" value={`${item.opportunityScore}`} />
                  <MiniMetric label="置信度" value={`${item.sourcingConfidence}%`} />
                  <MiniMetric label="反馈" value={`${item.feedbackCount}`} />
                </div>

                <div className="mb-3">
                  <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>平台建议</div>
                  <div className="flex flex-wrap gap-1">
                    {item.recommendedPlatforms.slice(0, 2).map((platform) => (
                      <Tag key={platform} style={{ borderRadius: 8, fontSize: 12 }}>
                        {platformLabels[platform]}
                      </Tag>
                    ))}
                    {item.providerNames.slice(0, 2).map((name) => (
                      <Tag key={name} color="blue" style={{ borderRadius: 8, fontSize: 12 }}>{name}</Tag>
                    ))}
                  </div>
                </div>

                <div className="mb-3">
                  <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>关键卖点</div>
                  <div className="flex flex-wrap gap-1">
                    {item.product.sellingPoints.slice(0, 3).map((sp) => (
                      <Tag key={sp} color="green" style={{ borderRadius: 8, fontSize: 12 }}>{sp}</Tag>
                    ))}
                    {item.product.sellingPoints.length === 0 && <Tag color="orange">待补卖点</Tag>}
                  </div>
                </div>

                <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                  <div className="text-xs mb-1" style={{ color: "var(--text-color-3)" }}>下一步动作</div>
                  <div className="text-sm" style={{ color: "var(--text-color-1)" }}>{item.nextAction}</div>
                  {item.validationMissing > 0 && (
                    <Tag color="orange" className="mt-2">待补 {item.validationMissing} 项验证</Tag>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                  <Button
                    type="text"
                    size="small"
                    onClick={(event) => {
                      event.stopPropagation();
                      router.push(`/generate?productId=${item.product.id}`);
                    }}
                  >
                    生成素材 <IconRight />
                  </Button>
                  <Button type="text" size="small" onClick={(event) => { event.stopPropagation(); openDetail(item.product); }}>
                    诊断
                  </Button>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="商品诊断"
        visible={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        style={{ width: 760 }}
      >
        {selectedProduct && selectedInsight && (
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex gap-4 min-w-0">
                <ProductImage visual={selectedInsight.visual} name={selectedProduct.name} />
                <div className="min-w-0">
                  <h3 className="text-lg font-semibold m-0" style={{ color: "var(--text-color-1)" }}>{selectedProduct.name}</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Tag color="blue">{selectedProduct.category}</Tag>
                    <OpportunityTag level={selectedInsight.level} />
                    <VisualRoleTag visual={selectedInsight.visual} />
                  </div>
                  <div className="text-xs mt-2" style={{ color: "var(--text-color-3)" }}>
                    图片来源：{selectedInsight.visual.imageSource} · 可信度 {selectedInsight.visual.confidence}%
                  </div>
                </div>
              </div>
              <ScoreBadge score={selectedInsight.opportunityScore} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MiniMetric label="资料完整度" value={`${selectedInsight.completeness}%`} />
              <MiniMetric label="跨境置信度" value={`${selectedInsight.sourcingConfidence}%`} />
              <MiniMetric label="反馈证据" value={`${selectedInsight.feedbackCount} 条`} />
              <MiniMetric label="已通过" value={`${selectedInsight.approvedCount} 条`} />
            </div>

            {selectedInsight.report && (
              <>
                <DiagnosticBlock title="外部验证">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                      <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>建议数据源</div>
                      <div className="flex flex-wrap gap-1">
                        {selectedInsight.recommendedProviderIds.map((providerId) => {
                          const provider = providerById.get(providerId);
                          return (
                            <Tag
                              key={providerId}
                              color="blue"
                              className="cursor-pointer"
                              onClick={() => provider && setSelectedProvider(provider)}
                            >
                              {provider?.name || providerId}
                            </Tag>
                          );
                        })}
                      </div>
                    </div>
                    <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                      <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>验证状态</div>
                      <div className="flex flex-wrap gap-1">
                        {selectedInsight.report.checks.map((check) => (
                          <Tag key={check.key} color={check.status === "passed" ? "green" : check.status === "missing" ? "orange" : "gold"}>
                            {check.label}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  </div>
                </DiagnosticBlock>

                <DiagnosticBlock title="数据来源贡献">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {selectedInsight.marketSources.slice(0, 6).map((source) => (
                      <MarketSourceCard
                        key={source.providerId}
                        source={source}
                        onClick={() => {
                          const provider = providerById.get(source.providerId);
                          if (provider) setSelectedProvider(provider);
                        }}
                      />
                    ))}
                  </div>
                </DiagnosticBlock>
              </>
            )}

            {selectedInsight.report && (
              <DiagnosticBlock title="机会信号">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {selectedInsight.report.signals.map((signal) => (
                    <div key={signal.key} className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{signal.label}</span>
                        <ScoreBadge score={signal.score} size="small" />
                      </div>
                      <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{signal.value}</div>
                    </div>
                  ))}
                </div>
              </DiagnosticBlock>
            )}

            <DiagnosticBlock title="平台打法">
              <div className="flex flex-wrap gap-2">
                {selectedInsight.recommendedPlatforms.map((platform) => (
                  <Tag key={platform} color="blue">{platformLabels[platform]}</Tag>
                ))}
              </div>
            </DiagnosticBlock>

            <DiagnosticBlock title="资料资产">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <TagGroup title="核心卖点" items={selectedProduct.sellingPoints} empty="待补卖点" color="green" />
                <TagGroup title="适用人群" items={selectedProduct.targetAudiences} empty="待补人群" color="purple" />
                <TagGroup title="使用场景" items={selectedProduct.usageScenarios} empty="待补场景" color="blue" />
                <TagGroup title="禁用表达" items={selectedProduct.forbiddenClaims} empty="建议补禁用词" color="red" />
              </div>
            </DiagnosticBlock>

            <DiagnosticBlock title="商品属性">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.entries(selectedProduct.attributes).map(([key, value]) => (
                  <div key={key} className="text-sm rounded-lg px-3 py-2" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <span style={{ color: "var(--text-color-3)" }}>{key}: </span>
                    <span style={{ color: "var(--text-color-1)" }}>{value}</span>
                  </div>
                ))}
                {Object.keys(selectedProduct.attributes).length === 0 && (
                  <span className="text-sm" style={{ color: "var(--text-color-3)" }}>暂无属性</span>
                )}
              </div>
            </DiagnosticBlock>

            <DiagnosticBlock title="待补短板">
              <div className="flex flex-wrap gap-2">
                {selectedInsight.gaps.map((gap) => <Tag key={gap} color="orange">{gap}</Tag>)}
                {selectedInsight.gaps.length === 0 && <Tag color="green">资料与反馈已满足基础生成</Tag>}
              </div>
            </DiagnosticBlock>

            {selectedInsight.report && (
              <DiagnosticBlock title="建议动作">
                <div className="space-y-2">
                  {selectedInsight.report.nextActions.map((action) => (
                    <div key={action} className="text-sm rounded-xl px-3 py-2" style={{ backgroundColor: "var(--color-fill-1)", color: "var(--text-color-1)" }}>
                      {action}
                    </div>
                  ))}
                </div>
              </DiagnosticBlock>
            )}

            <div className="flex gap-3 pt-4 border-t" style={{ borderColor: "var(--border-color-light)" }}>
              <Button type="primary" onClick={() => { setDetailVisible(false); router.push(`/generate?productId=${selectedProduct.id}`); }}>
                生成口碑素材
              </Button>
              <Button onClick={() => { setDetailVisible(false); router.push(`/feedback?productId=${selectedProduct.id}`); }}>
                补充反馈依据
              </Button>
              <Button onClick={() => setDetailVisible(false)}>关闭</Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        title="新增商品"
        visible={addVisible}
        onCancel={() => setAddVisible(false)}
        onOk={handleCreateProduct}
        okText="保存"
        style={{ width: 680 }}
      >
        <Form form={productForm} layout="vertical">
          <Row gutter={12}>
            <Col span={14}>
              <FormItem label="商品名称" field="name" rules={[{ required: true, message: "请输入商品名称" }]}>
                <Input placeholder="例: 静音破壁料理机 Pro" />
              </FormItem>
            </Col>
            <Col span={10}>
              <FormItem label="类目" field="category" rules={[{ required: true, message: "请选择类目" }]}>
                <Select placeholder="选择类目">
                  {["厨房电器", "家纺", "母婴用品", "食品饮料", "健康设备", "美妆护肤", "服饰鞋包", "家居日用"].map((category) => (
                    <Select.Option key={category} value={category}>{category}</Select.Option>
                  ))}
                </Select>
              </FormItem>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={14}>
              <FormItem label="商品图片 URL" field="imageUrl" help="优先填真实商品图；没有时系统会用免费图库场景图兜底">
                <Input placeholder="https://..." />
              </FormItem>
            </Col>
            <Col span={10}>
              <FormItem label="数据来源" field="sourceName">
                <Select placeholder="选择来源" allowClear>
                  {["人工录入", "Temu Seller Center", "TikTok Shop Seller Center", "海外仓表格", "供应链/1688", "店铺后台", "CSV导入"].map((source) => (
                    <Select.Option key={source} value={source}>{source}</Select.Option>
                  ))}
                </Select>
              </FormItem>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={14}>
              <FormItem label="来源链接" field="sourceUrl">
                <Input placeholder="商品页、榜单页、供应链页或素材页 URL" />
              </FormItem>
            </Col>
            <Col span={10}>
              <FormItem label="来源商品 ID" field="sourceProductId">
                <Input placeholder="ASIN / itemId / SKU / 条码" />
              </FormItem>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={8}>
              <FormItem label="参考价格" field="price">
                <Input placeholder="例: 29.99" />
              </FormItem>
            </Col>
            <Col span={8}>
              <FormItem label="币种" field="currency">
                <Select placeholder="币种" allowClear>
                  {["USD", "CNY", "EUR", "GBP", "JPY"].map((currency) => (
                    <Select.Option key={currency} value={currency}>{currency}</Select.Option>
                  ))}
                </Select>
              </FormItem>
            </Col>
            <Col span={8}>
              <FormItem label="采集方式" field="collectionMode">
                <Select placeholder="采集方式" allowClear>
                  <Select.Option value="人工录入">人工录入</Select.Option>
                  <Select.Option value="官方API">官方API</Select.Option>
                  <Select.Option value="CSV导入">CSV导入</Select.Option>
                  <Select.Option value="公开页面归档">公开页面归档</Select.Option>
                </Select>
              </FormItem>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <FormItem label="价格带" field="priceBand">
                <Select placeholder="选择价格带" allowClear>
                  <Select.Option value="引流款">引流款</Select.Option>
                  <Select.Option value="主推款">主推款</Select.Option>
                  <Select.Option value="利润款">利润款</Select.Option>
                  <Select.Option value="高客单">高客单</Select.Option>
                </Select>
              </FormItem>
            </Col>
            <Col span={12}>
              <FormItem label="主推平台" field="primaryPlatforms">
                <Select placeholder="选择平台" mode="multiple" allowClear>
                  {Object.entries(platformLabels).map(([key, label]) => (
                    <Select.Option key={key} value={key}>{label}</Select.Option>
                  ))}
                </Select>
              </FormItem>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <FormItem label="库存状态" field="inventoryStatus">
                <Select placeholder="选择库存状态" allowClear>
                  <Select.Option value="现货充足">现货充足</Select.Option>
                  <Select.Option value="少量现货">少量现货</Select.Option>
                  <Select.Option value="预售">预售</Select.Option>
                  <Select.Option value="清仓">清仓</Select.Option>
                </Select>
              </FormItem>
            </Col>
            <Col span={12}>
              <FormItem label="竞品差异" field="competitorEdge">
                <Input placeholder="例: 更安静、容量更大、清洗更方便" />
              </FormItem>
            </Col>
          </Row>

          <FormItem label="核心卖点" field="sellingPoints" help="每行一个卖点">
            <Input.TextArea placeholder="例:&#10;真静音降噪 42dB&#10;10叶精钢刀头&#10;12小时预约" rows={4} />
          </FormItem>
          <FormItem label="适用人群" field="targetAudiences">
            <Input placeholder="例: 宝妈家庭, 养生人群, 上班族" />
          </FormItem>
          <FormItem label="使用场景" field="usageScenarios">
            <Input placeholder="例: 早餐豆浆, 家庭使用, 送礼" />
          </FormItem>
          <FormItem label="禁用表达" field="forbiddenClaims" help="不允许在生成内容中出现的词汇">
            <Input placeholder="例: 治疗, 药用, 最安静" />
          </FormItem>
          <FormItem label="补充属性" field="attributes" help="每行一条，格式：属性名: 属性值">
            <Input.TextArea placeholder="例:&#10;材质: 高硼硅玻璃杯体&#10;容量: 1.75L&#10;颜色: 珍珠白" rows={3} />
          </FormItem>
        </Form>
      </Modal>

      <Modal
        title="数据源贡献说明"
        visible={!!selectedProvider}
        onCancel={() => setSelectedProvider(null)}
        footer={null}
        style={{ width: 720 }}
      >
        {selectedProvider && <ProviderDetail provider={selectedProvider} />}
      </Modal>
    </div>
  );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: "blue" | "green" | "cyan" | "orange" }) {
  const colors = {
    blue: "#3b82f6",
    green: "#10b981",
    cyan: "#06b6d4",
    orange: "#f97316",
  };
  return (
    <Col xs={12} md={6}>
      <Card style={{ borderRadius: 16 }}>
        <div className="text-sm" style={{ color: "var(--text-color-3)" }}>{label}</div>
        <div className="text-2xl font-bold mt-2" style={{ color: colors[tone] }}>{value}</div>
      </Card>
    </Col>
  );
}

function ProviderCard({ provider, onClick }: { provider: ProductResearchProvider; onClick: () => void }) {
  const channelLabels: Record<string, string> = {
    amazon: "Amazon",
    tiktok_shop: "TikTok Shop",
    tiktok_ads: "TikTok Ads",
    ads: "广告素材",
    independent: "独立站",
    marketplace: "平台商品",
    retail_api: "零售 API",
    open_data: "开放数据",
    trend: "趋势数据",
    image: "图片素材",
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left rounded-xl border p-3 cursor-pointer"
      style={{ borderColor: "var(--border-color)", backgroundColor: "var(--color-fill-1)" }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold" style={{ color: "var(--text-color-1)" }}>{provider.name}</div>
          <div className="mt-1 text-xs" style={{ color: "var(--text-color-3)" }}>
            {channelLabels[provider.channel] || provider.channel}
          </div>
        </div>
        <Tag color={provider.enabled ? "green" : "orange"}>{provider.enabled ? "可拉取" : "待配置"}</Tag>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        <Tag color={provider.freeTier ? "green" : "gray"}>{provider.freeTier ? "免费/开放" : "付费/订阅"}</Tag>
        <Tag color={levelColor(provider.automationLevel)}>自动化 {levelLabel(provider.automationLevel)}</Tag>
        <Tag color={levelColor(provider.dataQuality)}>质量 {levelLabel(provider.dataQuality)}</Tag>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {provider.coreSignals.slice(0, 3).map((signal) => (
          <Tag key={signal} style={{ borderRadius: 8, fontSize: 12 }}>{signal}</Tag>
        ))}
      </div>
    </button>
  );
}

function ProductImage({ visual, name, compact = false }: { visual: ProductVisual; name: string; compact?: boolean }) {
  return (
    <div
      className={compact ? "mb-4 overflow-hidden rounded-xl" : "overflow-hidden rounded-xl shrink-0"}
      style={{
        width: compact ? "100%" : 136,
        aspectRatio: compact ? "16 / 10" : "1 / 1",
        backgroundColor: "var(--color-fill-2)",
        backgroundImage: `url("${visual.imageUrl}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
      role="img"
      aria-label={name}
    />
  );
}

function VisualRoleTag({ visual }: { visual: ProductVisual }) {
  const meta = {
    product: { label: "真实商品图", color: "green" },
    marketplace: { label: "市场源图待拉取", color: "blue" },
    creative: { label: "素材图", color: "cyan" },
    scene_fallback: { label: "场景兜底图", color: "orange" },
  }[visual.imageRole];
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

function MarketSourceCard({ source, onClick }: { source: ProductMarketSource; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left rounded-xl border p-3 cursor-pointer"
      style={{ borderColor: "var(--border-color)", backgroundColor: "var(--color-fill-1)" }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold" style={{ color: "var(--text-color-1)" }}>{source.providerName}</div>
          <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{source.actionLabel}</div>
        </div>
        <ScoreBadge score={source.contributionScore} size="small" />
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        <Tag color={sourceStatusColor(source.status)}>{sourceStatusLabel(source.status)}</Tag>
        <Tag color={levelColor(source.automationLevel)}>自动化 {levelLabel(source.automationLevel)}</Tag>
        <Tag color={levelColor(source.dataQuality)}>质量 {levelLabel(source.dataQuality)}</Tag>
        <Tag color={imageSupportColor(source.imageSupport)}>{imageSupportLabel(source.imageSupport)}</Tag>
      </div>
      <p className="text-xs m-0 mt-2 line-clamp-2" style={{ color: "var(--text-color-3)" }}>{source.explanation}</p>
    </button>
  );
}

function CollectionStepCard({
  step,
  providerById,
  onProviderClick,
}: {
  step: ProductOpportunityReport["collectionPlan"][number];
  providerById: Map<string, ProductResearchProvider>;
  onProviderClick: (provider: ProductResearchProvider) => void;
}) {
  return (
    <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--text-color-1)" }}>{step.label}</div>
          <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{modeLabel(step.mode)} · {step.automationHint}</div>
        </div>
        <Tag color="blue">P{step.priority}</Tag>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {step.providerIds.map((providerId) => {
          const provider = providerById.get(providerId);
          return (
            <Tag
              key={providerId}
              color="blue"
              className={provider ? "cursor-pointer" : ""}
              onClick={() => provider && onProviderClick(provider)}
            >
              {provider?.name || providerId}
            </Tag>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {step.expectedFields.map((field) => <Tag key={field}>{field}</Tag>)}
      </div>
      <div className="text-xs mt-2" style={{ color: "var(--text-color-3)" }}>{step.qualityImpact}</div>
    </div>
  );
}

function ProviderDetail({ provider }: { provider: ProductResearchProvider }) {
  return (
    <div className="space-y-4">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-lg font-semibold m-0" style={{ color: "var(--text-color-1)" }}>{provider.name}</h3>
          <Tag color={provider.freeTier ? "green" : "gray"}>{provider.freeTier ? "免费/开放" : "付费/订阅"}</Tag>
          <Tag color={provider.enabled ? "green" : "orange"}>{provider.enabled ? "当前可用" : "待配置"}</Tag>
        </div>
        <p className="text-sm m-0 mt-2" style={{ color: "var(--text-color-2)" }}>{provider.contributionSummary}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MiniMetric label="自动化" value={levelLabel(provider.automationLevel)} />
        <MiniMetric label="数据质量" value={levelLabel(provider.dataQuality)} />
        <MiniMetric label="图片能力" value={imageSupportLabel(provider.imageSupport)} />
        <MiniMetric label="接入模式" value={provider.integrationMode} />
      </div>

      <TagGroup title="可贡献字段" items={provider.contributionFields} empty="暂无字段" color="blue" />
      <TagGroup title="核心信号" items={provider.coreSignals} empty="暂无信号" color="green" />
      <TagGroup title="适合场景" items={provider.bestFor} empty="暂无场景" color="purple" />
      <TagGroup title="采集方式" items={provider.collectionModes.map(modeLabel)} empty="暂无采集方式" color="cyan" />
      <TagGroup title="接入动作" items={provider.setupActions} empty="暂无动作" color="orange" />
      <TagGroup title="注意事项" items={provider.limitations} empty="暂无限制" color="red" />
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl px-3 py-2" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <div className="text-xs" style={{ color: "var(--text-color-3)" }}>{label}</div>
      <div className="text-sm font-semibold mt-1" style={{ color: "var(--text-color-1)" }}>{value}</div>
    </div>
  );
}

function OpportunityTag({ level }: { level: ProductInsight["level"] }) {
  const meta = {
    high: { label: "高机会", color: "green" },
    watch: { label: "可观察", color: "gold" },
    needs_evidence: { label: "待补证据", color: "orange" },
  }[level];
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

function DiagnosticBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <div className="text-sm font-medium mb-2" style={{ color: "var(--text-color-2)" }}>{title}</div>
      {children}
    </div>
  );
}

function TagGroup({ title, items, empty, color }: { title: string; items: string[]; empty: string; color: string }) {
  return (
    <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>{title}</div>
      <div className="flex flex-wrap gap-1">
        {items.map((item) => <Tag key={item} color={color}>{item}</Tag>)}
        {items.length === 0 && <Tag color="orange">{empty}</Tag>}
      </div>
    </div>
  );
}

function buildProductInsight(
  product: Product,
  feedbacks: Feedback[],
  tasks: GenerationTask[],
  contents: GeneratedContent[],
  report: ProductOpportunityReport | undefined,
  providerById: Map<string, ProductResearchProvider>
): ProductInsight {
  const productFeedbacks = feedbacks.filter((feedback) => feedback.productId === product.id);
  const productTasks = tasks.filter((task) => task.productId === product.id);
  const productContents = contents.filter((content) => productTasks.some((task) => task.id === content.taskId));
  const approvedCount = productContents.filter((content) => content.reviewStatus === "approved").length;
  const riskCount = productContents.filter((content) => content.riskFlags.length > 0).length;
  const avgScore = productContents.length
    ? Math.round(productContents.reduce((sum, content) => sum + content.score, 0) / productContents.length)
    : 0;
  const completeness = productCompleteness(product);
  const evidenceScore = Math.min(100, productFeedbacks.length * 34);
  const assetScore = Math.min(100, approvedCount * 35 + productContents.length * 12);
  const scoreSignal = avgScore || 70;
  const localOpportunityScore = clamp(
    Math.round(completeness * 0.34 + evidenceScore * 0.24 + assetScore * 0.18 + scoreSignal * 0.24 - riskCount * 8)
  );
  const reportMissingChecks = report?.checks.filter((check) => check.status === "missing").map((check) => check.label) || [];
  const gaps = [...productGaps(product, productFeedbacks.length, avgScore, riskCount), ...reportMissingChecks];
  const localLevel: ProductInsight["level"] = productFeedbacks.length === 0 || completeness < 55
    ? "needs_evidence"
    : localOpportunityScore >= 78
      ? "high"
      : "watch";
  const reportLevel: Record<ProductOpportunityReport["level"], ProductInsight["level"]> = {
    launch_candidate: "high",
    validate_more: "watch",
    needs_data: "needs_evidence",
  };
  const providerIds = report?.recommendedProviders || [];
  const visual = report?.visual || productVisualFromAttributes(product);

  return {
    product,
    feedbackCount: productFeedbacks.length,
    generationCount: productContents.length,
    approvedCount,
    riskCount,
    avgScore,
    completeness,
    opportunityScore: report?.score ?? localOpportunityScore,
    level: report ? reportLevel[report.level] : localLevel,
    recommendedPlatforms: recommendedPlatforms(product),
    gaps,
    nextAction: report?.nextActions[0] || nextAction(report ? reportLevel[report.level] : localLevel, productFeedbacks.length, approvedCount, riskCount),
    sourcingConfidence: report?.confidence ?? Math.min(100, Math.round(completeness * 0.65 + productFeedbacks.length * 18)),
    recommendedProviderIds: providerIds,
    providerNames: providerIds.map((providerId) => providerById.get(providerId)?.name || providerId),
    validationMissing: report?.checks.filter((check) => check.status === "missing").length ?? 0,
    visual,
    marketSources: report?.marketSources || [],
    collectionPlan: report?.collectionPlan || [],
    report,
  };
}

function productVisualFromAttributes(product: Product): ProductVisual {
  const imageUrl = firstAttribute(product, ["商品图片URL", "图片URL", "imageUrl", "sourceImageUrl", "商品主图"]);
  const sourceUrl = firstAttribute(product, ["来源链接", "sourceUrl", "商品链接", "采集URL"]);
  const sourceName = firstAttribute(product, ["数据来源", "sourceName", "市场平台", "marketplace"]) || "人工录入";
  if (imageUrl) {
    return {
      imageUrl,
      imageSource: sourceName,
      imageRole: "product",
      licenseNote: "人工录入或来源平台商品图，请确认授权与平台使用条款。",
      confidence: 90,
      sourceUrl,
    };
  }
  return {
    imageUrl: fallbackImage(product.category),
    imageSource: "免费图库兜底",
    imageRole: "scene_fallback",
    licenseNote: "免费图库场景图，仅用于视觉占位，不作为真实商品、销量或供应链证据。",
    confidence: 40,
  };
}

function productCompleteness(product: Product): number {
  const checks = [
    product.name,
    product.category,
    product.sellingPoints.length >= 2,
    product.targetAudiences.length > 0,
    product.usageScenarios.length > 0,
    product.forbiddenClaims.length > 0,
    Object.keys(product.attributes).length > 0,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function productGaps(product: Product, feedbackCount: number, avgScore: number, riskCount: number): string[] {
  const gaps: string[] = [];
  if (product.sellingPoints.length < 2) gaps.push("卖点不足");
  if (product.targetAudiences.length === 0) gaps.push("缺少人群");
  if (product.usageScenarios.length === 0) gaps.push("缺少场景");
  if (product.forbiddenClaims.length === 0) gaps.push("缺少禁用表达");
  if (feedbackCount === 0) gaps.push("缺少真实反馈");
  if (avgScore > 0 && avgScore < 75) gaps.push("内容质量偏低");
  if (riskCount > 0) gaps.push("已有风险素材待复核");
  return gaps;
}

function nextAction(level: ProductInsight["level"], feedbackCount: number, approvedCount: number, riskCount: number): string {
  if (feedbackCount === 0) return "先录入客户反馈，避免生成缺依据的一人称体验内容";
  if (riskCount > 0) return "先复核风险素材，再沉淀可复用口碑表达";
  if (approvedCount === 0) return "生成首批评价邀请、推荐语或详情页口碑素材";
  if (level === "high") return "适合扩展多平台、多风格口碑素材";
  return "继续补充反馈并观察生成质量";
}

function recommendedPlatforms(product: Product): Platform[] {
  const explicit = parsePlatforms(product.attributes["主推平台"]);
  if (explicit.length > 0) return explicit;
  const commerceExplicit = parsePlatforms(product.attributes["platforms"] || product.attributes["目标平台"]);
  if (commerceExplicit.length > 0) return commerceExplicit;
  if (product.attributes.temuStatus || product.attributes.tiktokStatus) return ["temu", "tiktok_shop"];
  if (product.category.includes("食品") || product.category.includes("美妆")) return ["xiaohongshu", "douyin", "taobao"];
  if (product.category.includes("母婴")) return ["xiaohongshu", "taobao", "jd"];
  if (product.category.includes("厨房") || product.category.includes("家居")) return ["taobao", "douyin", "pdd"];
  if (product.category.includes("健康")) return ["jd", "taobao", "douyin"];
  if (product.category.includes("家纺")) return ["taobao", "tmall", "xiaohongshu"];
  return ["taobao", "douyin"];
}

function parsePlatforms(value?: string): Platform[] {
  if (!value) return [];
  const aliases: Record<string, Platform> = {
    淘宝: "taobao",
    天猫: "tmall",
    京东: "jd",
    拼多多: "pdd",
    抖音: "douyin",
    小红书: "xiaohongshu",
    独立站: "independent",
    Temu: "temu",
    temu: "temu",
    TikTok: "tiktok_shop",
    "TikTok Shop": "tiktok_shop",
    tiktok: "tiktok_shop",
    tiktok_shop: "tiktok_shop",
    tiktokshop: "tiktok_shop",
    taobao: "taobao",
    tmall: "tmall",
    jd: "jd",
    pdd: "pdd",
    douyin: "douyin",
    xiaohongshu: "xiaohongshu",
    independent: "independent",
  };
  return splitComma(value).map((item) => aliases[item]).filter(Boolean);
}

function buildAttributes(values: Record<string, unknown>): Record<string, string> {
  return {
    ...parseAttributeLines(String(values.attributes || "")),
    ...(values.imageUrl ? { 商品图片URL: String(values.imageUrl) } : {}),
    ...(values.sourceUrl ? { 来源链接: String(values.sourceUrl) } : {}),
    ...(values.sourceName ? { 数据来源: String(values.sourceName) } : {}),
    ...(values.sourceProductId ? { 来源商品ID: String(values.sourceProductId) } : {}),
    ...(values.price ? { 参考价格: String(values.price) } : {}),
    ...(values.currency ? { 币种: String(values.currency) } : {}),
    ...(values.collectionMode ? { 采集方式: String(values.collectionMode) } : {}),
    ...(values.priceBand ? { 价格带: String(values.priceBand) } : {}),
    ...(values.inventoryStatus ? { 库存状态: String(values.inventoryStatus) } : {}),
    ...(values.competitorEdge ? { 竞品差异: String(values.competitorEdge) } : {}),
    ...(Array.isArray(values.primaryPlatforms) && values.primaryPlatforms.length
      ? { 主推平台: values.primaryPlatforms.map((platform) => platformLabels[platform as Platform] || platform).join("、") }
      : {}),
  };
}

function parseAttributeLines(value: string): Record<string, string> {
  return value
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((result, line) => {
      const [key, ...rest] = line.split(/[:：]/);
      const cleanKey = key?.trim();
      const cleanValue = rest.join(":").trim();
      if (cleanKey && cleanValue) result[cleanKey] = cleanValue;
      return result;
    }, {});
}

function splitLines(value?: string): string[] {
  return (value || "")
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitComma(value?: string): string[] {
  return (value || "")
    .split(/[,，、]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function firstAttribute(product: Product, keys: string[]): string {
  for (const key of keys) {
    const value = product.attributes[key];
    if (value?.trim()) return value.trim();
  }
  return "";
}

function fallbackImage(category: string): string {
  if (category.includes("厨房") || category.includes("电器")) {
    return "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("家纺") || category.includes("床品")) {
    return "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("家居") || category.includes("日用")) {
    return "https://images.unsplash.com/photo-1513161455079-7dc1de15ef3e?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("食品") || category.includes("饮料")) {
    return "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0f?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("美妆")) {
    return "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("服饰")) {
    return "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("健康")) {
    return "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=900&q=80";
  }
  if (category.includes("母婴")) {
    return "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?auto=format&fit=crop&w=900&q=80";
  }
  return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80";
}

function levelLabel(level: "high" | "medium" | "low"): string {
  return { high: "高", medium: "中", low: "低" }[level];
}

function levelColor(level: "high" | "medium" | "low"): string {
  return { high: "green", medium: "blue", low: "orange" }[level];
}

function imageSupportLabel(value: ProductResearchProvider["imageSupport"]): string {
  return {
    product_image: "真实商品图",
    creative_image: "素材/趋势图",
    scene_image: "场景兜底图",
    none: "无图片",
  }[value];
}

function imageSupportColor(value: ProductResearchProvider["imageSupport"]): string {
  return {
    product_image: "green",
    creative_image: "cyan",
    scene_image: "orange",
    none: "gray",
  }[value];
}

function sourceStatusLabel(status: ProductMarketSource["status"]): string {
  return {
    ready: "可自动拉取",
    needs_key: "待配置 Key",
    manual: "人工/导入",
    fallback: "兜底图",
  }[status];
}

function sourceStatusColor(status: ProductMarketSource["status"]): string {
  return {
    ready: "green",
    needs_key: "orange",
    manual: "blue",
    fallback: "gold",
  }[status];
}

function modeLabel(mode: string): string {
  return {
    official_api: "官方 API",
    manual_input: "人工录入",
    public_page_capture: "公开页面归档",
    csv_import: "CSV 导入",
    fallback_image: "图片兜底",
    api_or_export: "API/导出",
    official_free: "官方免费",
    official_manual: "官方手动",
  }[mode] || mode;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}
