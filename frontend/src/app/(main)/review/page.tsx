"use client";
import { useState, useMemo } from "react";
import { Card, Button, Tag, Select, Input, Modal, Message } from "@arco-design/web-react";
import {
  IconCheckCircle,
  IconSearch,
  IconRight,
  IconRefresh,
  IconCopy,
  IconDownload,
  IconEye,
} from "@arco-design/web-react/icon";
import { useRouter } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import PageHeader from "@/components/common/PageHeader";
import ScoreBadge from "@/components/common/ScoreBadge";
import ReviewStatusTag from "@/components/common/ReviewStatusTag";
import QualityBar from "@/components/common/QualityBar";
import RiskTag from "@/components/common/RiskTag";
import EmptyState from "@/components/common/EmptyState";
import { ContentTypeTag, PlatformTag } from "@/components/common/ConfigTags";
import { platformLabels, type GeneratedContent, type Platform } from "@/lib/types";

type RiskFilter = "all" | "has_risk" | "safe_alternative" | "high_score";

export default function ReviewPage() {
  const router = useRouter();
  const { tasks, contents, updateContentReview } = useDataStore();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [platformFilter, setPlatformFilter] = useState<Platform | undefined>();
  const [search, setSearch] = useState("");
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedContent, setSelectedContent] = useState<GeneratedContent | null>(null);

  const filteredContents = useMemo(() => {
    return contents.filter((c) => {
      const task = tasks.find((t) => t.id === c.taskId);
      const matchStatus = !statusFilter || c.reviewStatus === statusFilter;
      const matchPlatform = !platformFilter || task?.config.platform === platformFilter;
      const matchRisk =
        riskFilter === "all" ||
        (riskFilter === "has_risk" && c.riskFlags.length > 0) ||
        (riskFilter === "safe_alternative" && c.riskFlags.includes("safe_alternative_generated")) ||
        (riskFilter === "high_score" && c.score >= 85 && c.riskFlags.length === 0);
      const matchSearch = !search || c.text.includes(search) || task?.productName?.includes(search);
      return matchStatus && matchPlatform && matchRisk && matchSearch;
    });
  }, [contents, platformFilter, riskFilter, search, statusFilter, tasks]);

  const statusCounts = useMemo(() => ({
    all: contents.length,
    pending: contents.filter((c) => c.reviewStatus === "pending").length,
    approved: contents.filter((c) => c.reviewStatus === "approved").length,
    rejected: contents.filter((c) => c.reviewStatus === "rejected").length,
  }), [contents]);

  const reviewSummary = useMemo(() => ({
    highScore: contents.filter((content) => content.score >= 85 && content.riskFlags.length === 0).length,
    risky: contents.filter((content) => content.riskFlags.length > 0).length,
    safeAlternative: contents.filter((content) => content.riskFlags.includes("safe_alternative_generated")).length,
    averageScore: contents.length
      ? Math.round(contents.reduce((sum, content) => sum + content.score, 0) / contents.length)
      : 0,
  }), [contents]);

  const handleApprove = async (id: string) => {
    try {
      await updateContentReview(id, "approved");
      Message.success("已通过");
      if (detailVisible) setDetailVisible(false);
    } catch (error) {
      Message.error(error instanceof Error ? error.message : "审核提交失败");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await updateContentReview(id, "rejected");
      Message.info("已驳回");
      if (detailVisible) setDetailVisible(false);
    } catch (error) {
      Message.error(error instanceof Error ? error.message : "审核提交失败");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    Message.success("已复制到剪贴板");
  };

  const handleExportApproved = () => {
    const approved = contents.filter((content) => content.reviewStatus === "approved");
    if (approved.length === 0) {
      Message.warning("暂无已通过内容");
      return;
    }
    const lines = approved.map((content, index) => {
      const task = tasks.find((item) => item.id === content.taskId);
      return [
        `#${index + 1} ${task?.productName || "未知商品"} / ${task?.config.platform ? platformLabels[task.config.platform] : "未知平台"}`,
        `质量分: ${content.score}`,
        content.text,
      ].join("\n");
    });
    const blob = new Blob([lines.join("\n\n---\n\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `reviewpilot-approved-${new Date().toISOString().slice(0, 10)}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
    Message.success(`已导出 ${approved.length} 条通过内容`);
  };

  const openDetail = (content: GeneratedContent) => {
    setSelectedContent(content);
    setDetailVisible(true);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="审核中心"
        subtitle="审核、编辑和管理生成的口碑内容"
        icon={<IconCheckCircle />}
        extra={
          <Button icon={<IconDownload />} onClick={handleExportApproved}>
            导出通过内容
          </Button>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <ReviewMetric label="高质量可用" value={reviewSummary.highScore} color="#10b981" />
        <ReviewMetric label="风险素材" value={reviewSummary.risky} color="#f97316" />
        <ReviewMetric label="安全替代" value={reviewSummary.safeAlternative} color="#3b82f6" />
        <ReviewMetric label="平均质量分" value={reviewSummary.averageScore} color="#8b5cf6" />
      </div>

      {/* Status tabs */}
      <Card className="mb-6" style={{ borderRadius: 16 }}>
        <div className="flex flex-wrap items-center gap-3">
          {[
            { key: undefined, label: "全部", count: statusCounts.all },
            { key: "pending", label: "待审核", count: statusCounts.pending },
            { key: "approved", label: "已通过", count: statusCounts.approved },
            { key: "rejected", label: "已驳回", count: statusCounts.rejected },
          ].map((tab) => (
            <button
              key={tab.label}
              type="button"
              onClick={() => setStatusFilter(tab.key)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border-0 cursor-pointer transition-all"
              style={{
                backgroundColor: statusFilter === tab.key ? "rgba(249, 115, 22, 0.12)" : "var(--color-fill-1)",
                color: statusFilter === tab.key ? "var(--color-primary)" : "var(--text-color-2)",
                fontWeight: statusFilter === tab.key ? 600 : 400,
              }}
            >
              {tab.label}
              <span
                className="grid h-5 min-w-5 place-items-center rounded-full px-1.5 text-xs"
                style={{
                  backgroundColor: statusFilter === tab.key ? "rgba(249, 115, 22, 0.2)" : "var(--color-fill-2)",
                }}
              >
                {tab.count}
              </span>
            </button>
          ))}
          <div className="flex-1" />
          <Select value={riskFilter} onChange={setRiskFilter} style={{ width: 150 }}>
            <Select.Option value="all">全部质量</Select.Option>
            <Select.Option value="high_score">高质量可用</Select.Option>
            <Select.Option value="has_risk">有风险标记</Select.Option>
            <Select.Option value="safe_alternative">安全替代</Select.Option>
          </Select>
          <Select placeholder="全部平台" value={platformFilter} onChange={setPlatformFilter} allowClear style={{ width: 140 }}>
            {Object.entries(platformLabels).map(([key, label]) => (
              <Select.Option key={key} value={key}>{label}</Select.Option>
            ))}
          </Select>
          <Input
            prefix={<IconSearch style={{ color: "var(--text-color-4)" }} />}
            placeholder="搜索内容..."
            value={search}
            onChange={setSearch}
            style={{ width: 240 }}
          />
        </div>
      </Card>

      {/* Content list */}
      {filteredContents.length === 0 ? (
        <EmptyState
          icon="📋"
          title="暂无内容"
          description="生成的内容会显示在这里等待审核"
          actionText="去生成"
          onAction={() => router.push("/generate")}
        />
      ) : (
        <div className="space-y-4">
          {filteredContents.map((content, index) => {
            const task = tasks.find((t) => t.id === content.taskId);
            return (
              <Card
                key={content.id}
                className="hover-lift animate-fade-in"
                style={{ borderRadius: 16, animationDelay: `${index * 40}ms` }}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <span className="font-semibold text-sm" style={{ color: "var(--text-color-1)" }}>
                        {task?.productName || "未知商品"}
                      </span>
                      {task?.config.contentType && <ContentTypeTag type={task.config.contentType} />}
                      {task?.config.platform && <PlatformTag platform={task.config.platform} />}
                      <ScoreBadge score={content.score} size="small" />
                      <ReviewStatusTag status={content.reviewStatus} />
                      <RiskTag flags={content.riskFlags} />
                    </div>

                    {/* Content text */}
                    <p className="text-sm leading-relaxed mb-3" style={{ color: "var(--text-color-2)" }}>
                      {content.text}
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs" style={{ color: "var(--text-color-4)" }}>
                          {new Date(content.createdAt).toLocaleDateString("zh-CN")}
                        </span>
                        <span className="text-xs" style={{ color: "var(--text-color-4)" }}>
                          来源: {content.sourceTrace.length} 项依据
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button type="text" size="small" icon={<IconEye />} onClick={() => openDetail(content)}>
                          详情
                        </Button>
                        <Button type="text" size="small" icon={<IconCopy />} onClick={() => handleCopy(content.text)}>
                          复制
                        </Button>
                        {content.reviewStatus === "pending" && (
                          <>
                            <Button type="primary" size="small" onClick={() => handleApprove(content.id)}>
                              通过
                            </Button>
                            <Button status="danger" size="small" onClick={() => handleReject(content.id)}>
                              驳回
                            </Button>
                          </>
                        )}
                        {content.reviewStatus === "approved" && (
                          <Button type="text" size="small" icon={<IconCopy />} onClick={() => handleCopy(content.text)}>
                            复制使用
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detail modal */}
      <Modal
        title="内容详情"
        visible={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        style={{ width: 700 }}
      >
        {selectedContent && (() => {
          const task = tasks.find((t) => t.id === selectedContent.taskId);
          return (
            <div className="space-y-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold">{task?.productName || "未知商品"}</span>
                {task?.config.contentType && <ContentTypeTag type={task.config.contentType} />}
                {task?.config.platform && <PlatformTag platform={task.config.platform} />}
                <ScoreBadge score={selectedContent.score} />
                <ReviewStatusTag status={selectedContent.reviewStatus} />
              </div>
              <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-xs mb-2" style={{ color: "var(--text-color-3)" }}>审核建议</div>
                <div className="text-sm" style={{ color: "var(--text-color-2)" }}>
                  {reviewAdvice(selectedContent)}
                </div>
              </div>

              <div className="p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <p className="text-sm leading-relaxed m-0" style={{ color: "var(--text-color-2)" }}>
                  {selectedContent.text}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button type="text" size="small" icon={<IconCopy />} onClick={() => handleCopy(selectedContent.text)}>
                  复制文本
                </Button>
              </div>

              <RiskTag flags={selectedContent.riskFlags} />

              {/* Quality report */}
              <div className="p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-sm font-medium mb-3" style={{ color: "var(--text-color-2)" }}>质量报告</div>
                <div className="space-y-2">
                  <QualityBar label="自然度" value={selectedContent.qualityReport.naturalness} />
                  <QualityBar label="具体度" value={selectedContent.qualityReport.specificity} />
                  <QualityBar label="事实一致" value={selectedContent.qualityReport.factConsistency} />
                  <QualityBar label="平台适配" value={selectedContent.qualityReport.platformFit} />
                  <QualityBar label="重复风险" value={100 - selectedContent.qualityReport.repetitionRisk} />
                  <QualityBar label="夸大风险" value={100 - selectedContent.qualityReport.exaggerationRisk} />
                </div>
              </div>

              {/* Source trace */}
              <div>
                <div className="text-sm font-medium mb-2" style={{ color: "var(--text-color-2)" }}>来源依据</div>
                <div className="flex flex-wrap gap-2">
                  {selectedContent.sourceTrace.map((trace) => (
                    <Tag key={trace} style={{ borderRadius: 8 }}>{trace}</Tag>
                  ))}
                </div>
              </div>

              {/* Actions */}
              {selectedContent.reviewStatus === "pending" && (
                <div className="flex gap-3 pt-4 border-t" style={{ borderColor: "var(--border-color-light)" }}>
                  <Button type="primary" onClick={() => handleApprove(selectedContent.id)}>
                    <IconCheckCircle /> 通过
                  </Button>
                  <Button status="danger" onClick={() => handleReject(selectedContent.id)}>
                    驳回
                  </Button>
                  <Button icon={<IconRefresh />}>
                    请求重写
                  </Button>
                </div>
              )}
            </div>
          );
        })()}
      </Modal>
    </div>
  );
}

function ReviewMetric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card style={{ borderRadius: 16 }}>
      <div className="text-xs" style={{ color: "var(--text-color-3)" }}>{label}</div>
      <div className="text-2xl font-bold mt-2" style={{ color }}>{value}</div>
    </Card>
  );
}

function reviewAdvice(content: GeneratedContent): string {
  if (content.riskFlags.includes("safe_alternative_generated")) {
    return "这是安全替代话术，适合评价邀请或客服回访，不建议当作用户好评直接发布。";
  }
  if (content.riskFlags.length > 0) {
    return "存在风险标记，建议先核对来源依据、禁用表达和平台规则，再决定通过或重写。";
  }
  if (content.score >= 85) {
    return "质量分高且无风险标记，可优先复制使用或沉淀为商品常用好评模板。";
  }
  if (content.score >= 70) {
    return "基础可用，建议人工微调语气和细节后再通过。";
  }
  return "质量偏低，建议驳回或请求重写。";
}
