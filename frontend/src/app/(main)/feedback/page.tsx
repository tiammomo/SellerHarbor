"use client";
import { useEffect, useState, useMemo } from "react";
import { Card, Button, Tag, Input, Select, Grid, Modal, Form, Message, Timeline } from "@arco-design/web-react";
import {
  IconPlus,
  IconSearch,
  IconMessage,
  IconRight,
  IconCheckCircle,
  IconInfoCircle,
} from "@arco-design/web-react/icon";
import { useRouter } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";

const { Row, Col } = Grid;
const FormItem = Form.Item;

const sourceTypeLabels: Record<string, { label: string; color: string; icon: string }> = {
  customer_review: { label: "客户评价", color: "blue", icon: "⭐" },
  cs_summary: { label: "客服回访", color: "green", icon: "🎧" },
  after_sales: { label: "售后反馈", color: "orange", icon: "🔧" },
  authorized: { label: "授权反馈", color: "purple", icon: "✅" },
};

export default function FeedbackPage() {
  const router = useRouter();
  const { feedbacks, products, createFeedback } = useDataStore();
  const [feedbackForm] = Form.useForm();
  const [search, setSearch] = useState("");
  const [productFilter, setProductFilter] = useState<string | undefined>();
  const [addVisible, setAddVisible] = useState(false);

  useEffect(() => {
    const productId = new URLSearchParams(window.location.search).get("productId") || undefined;
    if (productId) {
      setProductFilter(productId);
      feedbackForm.setFieldValue("productId", productId);
    }
  }, [feedbackForm]);

  const filteredFeedbacks = useMemo(() => {
    return feedbacks.filter((f) => {
      const matchSearch = !search || f.sourceSummary.includes(search) || f.productName?.includes(search);
      const matchProduct = !productFilter || f.productId === productFilter;
      return matchSearch && matchProduct;
    });
  }, [feedbacks, search, productFilter]);

  const handleCreateFeedback = async () => {
    try {
      const values = await feedbackForm.validate();
      await createFeedback({
        productId: values.productId,
        sourceType: values.sourceType,
        sourceSummary: values.sourceSummary,
        confirmedFacts: splitLines(values.confirmedFacts),
        subjectiveOpinions: splitLines(values.subjectiveOpinions),
        consentStatus: values.consentStatus || "confirmed",
      });
      Message.success("反馈已录入");
      feedbackForm.resetFields();
      setAddVisible(false);
    } catch (error) {
      if (error instanceof Error) {
        Message.error(error.message);
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="反馈录入"
        subtitle="管理客户授权反馈、客服回访摘要和售后记录"
        icon={<IconMessage />}
        extra={
          <Button type="primary" icon={<IconPlus />} onClick={() => setAddVisible(true)}>
            录入反馈
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6" style={{ borderRadius: 16 }}>
        <div className="flex flex-wrap items-center gap-4">
          <Input
            prefix={<IconSearch style={{ color: "var(--text-color-4)" }} />}
            placeholder="搜索反馈内容..."
            value={search}
            onChange={setSearch}
            style={{ width: 280 }}
          />
          <Select
            placeholder="全部商品"
            value={productFilter}
            onChange={setProductFilter}
            allowClear
            style={{ width: 200 }}
          >
            {products.map((p) => (
              <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
            ))}
          </Select>
          <div className="flex-1" />
          <span className="text-sm" style={{ color: "var(--text-color-3)" }}>
            共 {filteredFeedbacks.length} 条反馈
          </span>
        </div>
      </Card>

      {/* Feedback list */}
      {filteredFeedbacks.length === 0 ? (
        <EmptyState
          icon="💬"
          title="暂无反馈"
          description="录入客户反馈后可以作为生成内容的真实依据"
          actionText="录入反馈"
          onAction={() => setAddVisible(true)}
        />
      ) : (
        <div className="space-y-4">
          {filteredFeedbacks.map((feedback, index) => {
            const sourceMeta = sourceTypeLabels[feedback.sourceType] || sourceTypeLabels.customer_review;
            return (
              <Card
                key={feedback.id}
                className="hover-lift animate-fade-in"
                style={{ borderRadius: 16, animationDelay: `${index * 60}ms` }}
              >
                <div className="flex items-start gap-4">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                    style={{ backgroundColor: "var(--color-fill-1)" }}
                  >
                    {sourceMeta.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-sm" style={{ color: "var(--text-color-1)" }}>
                        {feedback.productName || "未知商品"}
                      </span>
                      <Tag color={sourceMeta.color}>{sourceMeta.label}</Tag>
                      {feedback.consentStatus === "confirmed" && (
                        <Tag color="green">已授权</Tag>
                      )}
                    </div>

                    <p className="text-sm mb-3 leading-relaxed" style={{ color: "var(--text-color-2)" }}>
                      {feedback.sourceSummary}
                    </p>

                    <Row gutter={16}>
                      <Col xs={24} md={12}>
                        <div className="mb-2">
                          <span className="text-xs font-medium flex items-center gap-1" style={{ color: "var(--color-success)" }}>
                            <IconCheckCircle /> 已确认事实
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {feedback.confirmedFacts.map((fact) => (
                              <Tag key={fact} color="green" style={{ borderRadius: 8, fontSize: 12 }}>{fact}</Tag>
                            ))}
                          </div>
                        </div>
                      </Col>
                      <Col xs={24} md={12}>
                        <div className="mb-2">
                          <span className="text-xs font-medium flex items-center gap-1" style={{ color: "var(--color-info)" }}>
                            <IconInfoCircle /> 主观感受
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {feedback.subjectiveOpinions.map((op) => (
                              <Tag key={op} color="blue" style={{ borderRadius: 8, fontSize: 12 }}>{op}</Tag>
                            ))}
                          </div>
                        </div>
                      </Col>
                    </Row>

                    <div className="flex items-center justify-between mt-3 pt-3 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                      <span className="text-xs" style={{ color: "var(--text-color-4)" }}>
                        {new Date(feedback.createdAt).toLocaleDateString("zh-CN")} · {new Date(feedback.createdAt).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <Button
                        type="text"
                        size="small"
                        style={{ color: "var(--color-primary)" }}
                        onClick={() => router.push(`/generate?productId=${feedback.productId}&feedbackId=${feedback.id}`)}
                      >
                        用于生成 <IconRight />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add feedback modal */}
      <Modal
        title="录入反馈"
        visible={addVisible}
        onCancel={() => setAddVisible(false)}
        onOk={handleCreateFeedback}
        okText="保存"
        style={{ width: 600 }}
      >
        <Form form={feedbackForm} layout="vertical">
          <FormItem label="关联商品" field="productId" rules={[{ required: true, message: "请选择商品" }]}>
            <Select placeholder="选择商品">
              {products.map((p) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </FormItem>
          <FormItem label="反馈来源" field="sourceType" rules={[{ required: true, message: "请选择来源类型" }]}>
            <Select placeholder="选择来源类型">
              <Select.Option value="customer_review">客户评价</Select.Option>
              <Select.Option value="cs_summary">客服回访</Select.Option>
              <Select.Option value="after_sales">售后反馈</Select.Option>
              <Select.Option value="authorized">授权反馈</Select.Option>
            </Select>
          </FormItem>
          <FormItem label="反馈摘要" field="sourceSummary" rules={[{ required: true, message: "请输入反馈摘要" }]}>
            <Input.TextArea placeholder="粘贴或整理客户反馈的核心内容..." rows={5} />
          </FormItem>
          <FormItem label="已确认事实" field="confirmedFacts" help="每行一条可验证的事实">
            <Input.TextArea placeholder="例:&#10;可正常使用预约功能&#10;自清洗功能可用&#10;可制作辅食" rows={3} />
          </FormItem>
          <FormItem label="主观感受" field="subjectiveOpinions" help="每行一条客户主观感受">
            <Input.TextArea placeholder="例:&#10;比老机器安静&#10;清洗省事&#10;打出来很细腻" rows={3} />
          </FormItem>
          <FormItem label="授权状态" field="consentStatus" initialValue="confirmed">
            <Select placeholder="选择授权状态" defaultValue="confirmed">
              <Select.Option value="confirmed">已确认授权</Select.Option>
              <Select.Option value="pending">待确认</Select.Option>
              <Select.Option value="not_required">不需要授权</Select.Option>
            </Select>
          </FormItem>
        </Form>
      </Modal>
    </div>
  );
}

function splitLines(value?: string): string[] {
  return (value || "")
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
}
