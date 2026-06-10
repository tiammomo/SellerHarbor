"use client";
import { useMemo } from "react";
import { Card, Grid, Button, Tag, Skeleton } from "@arco-design/web-react";
import {
  IconRight,
  IconArrowRise,
  IconApps,
  IconMessage,
  IconEdit,
  IconCheckCircle,
  IconDashboard,
  IconExclamationCircle,
  IconFile,
  IconStorage,
  IconEye,
} from "@arco-design/web-react/icon";
import ReactECharts from "echarts-for-react";
import { useRouter } from "next/navigation";
import { useDataStore } from "@/lib/stores/dataStore";
import ScoreBadge from "@/components/common/ScoreBadge";
import ReviewStatusTag from "@/components/common/ReviewStatusTag";
import { ContentTypeTag, PlatformTag } from "@/components/common/ConfigTags";

const { Row, Col } = Grid;

export default function DashboardPage() {
  const router = useRouter();
  const { products, feedbacks, tasks, contents, dashboardStats } = useDataStore();

  const pendingContents = useMemo(() => contents.filter((c) => c.reviewStatus === "pending"), [contents]);
  const recentContents = useMemo(() => [...contents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 5), [contents]);

  const statCards = [
    {
      label: "商品总数",
      value: dashboardStats.totalProducts,
      icon: <IconApps />,
      iconColor: "#f97316",
      iconBg: "#f9731618",
      gradient: "primary",
      trend: "+2",
      trendUp: true,
    },
    {
      label: "反馈录入",
      value: dashboardStats.totalFeedbacks,
      icon: <IconMessage />,
      iconColor: "#10b981",
      iconBg: "#10b98118",
      gradient: "success",
      trend: "+3",
      trendUp: true,
    },
    {
      label: "生成内容",
      value: dashboardStats.totalGenerations,
      icon: <IconEdit />,
      iconColor: "#3b82f6",
      iconBg: "#3b82f618",
      gradient: "info",
      trend: "+5",
      trendUp: true,
    },
    {
      label: "待审核",
      value: dashboardStats.pendingReviews,
      icon: <IconExclamationCircle />,
      iconColor: "#f59e0b",
      iconBg: "#f59e0b18",
      gradient: "warning",
      trend: "-1",
      trendUp: false,
    },
  ];

  const quickActions = [
    { icon: <IconEdit />, label: "生成内容", path: "/generate", bg: "linear-gradient(135deg, #f97316 0%, #f59e0b 100%)" },
    { icon: <IconApps />, label: "商品管理", path: "/products", bg: "linear-gradient(135deg, #10b981 0%, #059669 100%)" },
    { icon: <IconMessage />, label: "反馈录入", path: "/feedback", bg: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)" },
    { icon: <IconCheckCircle />, label: "审核中心", path: "/review", bg: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" },
    { icon: <IconStorage />, label: "品牌话术", path: "/knowledge", bg: "linear-gradient(135deg, #d97706 0%, #b45309 100%)" },
    { icon: <IconFile />, label: "生成记录", path: "/history", bg: "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)" },
  ];

  const chartOption = {
    tooltip: { trigger: "axis" as const },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: {
      type: "category" as const,
      data: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
      axisLine: { lineStyle: { color: "#94a3b8" } },
      axisLabel: { color: "#64748b" },
    },
    yAxis: {
      type: "value" as const,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "#e2e8f0", type: "dashed" as const } },
      axisLabel: { color: "#64748b" },
    },
    series: [
      {
        data: dashboardStats.weeklyGenerations,
        type: "line" as const,
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#f97316", width: 3 },
        itemStyle: { color: "#f97316" },
        areaStyle: {
          color: {
            type: "linear" as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(249, 115, 22, 0.25)" },
              { offset: 1, color: "rgba(249, 115, 22, 0.02)" },
            ],
          },
        },
      },
    ],
  };

  const scoreDistOption = {
    tooltip: { trigger: "item" as const },
    legend: { bottom: 0, textStyle: { color: "#64748b" } },
    series: [
      {
        type: "pie" as const,
        radius: ["45%", "70%"],
        center: ["50%", "45%"],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: "#fff", borderWidth: 2 },
        label: { show: false },
        data: [
          { value: 4, name: "优秀 (85+)", itemStyle: { color: "#10b981" } },
          { value: 3, name: "良好 (70-84)", itemStyle: { color: "#3b82f6" } },
          { value: 2, name: "一般 (55-69)", itemStyle: { color: "#f59e0b" } },
          { value: 1, name: "较差 (<55)", itemStyle: { color: "#ef4444" } },
        ],
      },
    ],
  };

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      {/* Stat cards */}
      <Row gutter={16} className="dashboard-card-row mb-6">
        {statCards.map((card, index) => (
          <Col key={index} xs={12} sm={12} md={6} className="dashboard-card-col">
            <div
              className={`stat-card dashboard-metric-card animate-fade-in ${card.gradient}`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="dashboard-card-icon" style={{ color: card.iconColor, backgroundColor: card.iconBg }}>
                  {card.icon}
                </span>
                <div
                  className="flex items-center gap-1 text-xs px-2 py-1 rounded-full"
                  style={{
                    backgroundColor: card.trendUp ? "#10b98120" : "#ef444420",
                    color: card.trendUp ? "#10b981" : "#ef4444",
                  }}
                >
                  {card.trendUp ? <IconArrowRise /> : <IconArrowRise style={{ transform: "rotate(180deg)" }} />}
                  {card.trend}
                </div>
              </div>
              <div className="text-sm mb-1" style={{ color: "var(--text-color-3)" }}>{card.label}</div>
              <div className="text-2xl font-bold" style={{ color: "var(--text-color-1)" }}>{card.value}</div>
            </div>
          </Col>
        ))}
      </Row>

      {/* Quality overview + Chart */}
      <Row gutter={16} className="mb-6">
        <Col xs={24} md={12}>
          <Card style={{ borderRadius: 16 }} title={<div className="flex items-center gap-2"><IconDashboard /><span>质量概览</span></div>}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-3xl font-bold" style={{ color: "var(--color-primary)" }}>{dashboardStats.averageScore}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>平均质量分</div>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-3xl font-bold" style={{ color: "var(--color-success)" }}>{dashboardStats.approvedToday}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>今日通过</div>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-3xl font-bold" style={{ color: "var(--color-warning)" }}>{dashboardStats.pendingReviews}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>待审核</div>
              </div>
              <div className="text-center p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-3xl font-bold" style={{ color: "var(--color-danger)" }}>{dashboardStats.riskIntercepted}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>风险拦截</div>
              </div>
            </div>
            <ReactECharts option={scoreDistOption} style={{ height: 200 }} />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card style={{ borderRadius: 16 }} title={<div className="flex items-center gap-2"><IconStorage /><span>本周生成趋势</span></div>}>
            <ReactECharts option={chartOption} style={{ height: 320 }} />
          </Card>
        </Col>
      </Row>

      {/* Quick actions */}
      <Card className="mb-6" style={{ borderRadius: 16 }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: "var(--text-color-1)" }}>快捷入口</h3>
        </div>
        <Row gutter={16}>
          {quickActions.map((action, index) => (
            <Col key={action.path} xs={12} sm={6} md={4}>
              <div
                className="quick-action-btn mb-4 animate-fade-in"
                style={{ animationDelay: `${index * 100 + 200}ms` }}
                onClick={() => router.push(action.path)}
              >
                <div className="icon-wrapper text-2xl" style={{ background: action.bg }}>{action.icon}</div>
                <span className="text-sm font-medium" style={{ color: "var(--text-color-2)" }}>{action.label}</span>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      <Row gutter={16}>
        {/* Recent generated content */}
        <Col xs={24} md={16}>
          <Card
            style={{ borderRadius: 16 }}
            title={<div className="flex items-center gap-2"><IconEye /><span>最近生成内容</span></div>}
            extra={
              <Button type="text" size="small" onClick={() => router.push("/review")} style={{ color: "var(--color-primary)" }}>
                查看全部 <IconRight />
              </Button>
            }
          >
            <div className="space-y-2">
              {recentContents.map((content, index) => {
                const task = tasks.find((t) => t.id === content.taskId);
                return (
                  <div
                    key={content.id}
                    className="content-item animate-fade-in"
                    style={{ animationDelay: `${index * 50 + 300}ms` }}
                    onClick={() => router.push("/review")}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0"
                        style={{ backgroundColor: "#f9731620" }}
                      >
                        ✍️
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-sm truncate" style={{ color: "var(--text-color-1)" }}>
                          {task?.productName || "未知商品"}
                        </div>
                        <div className="text-xs truncate mt-0.5" style={{ color: "var(--text-color-3)" }}>
                          {content.text.slice(0, 60)}...
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <ScoreBadge score={content.score} size="small" />
                      <ReviewStatusTag status={content.reviewStatus} />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>

        {/* Pending reviews */}
        <Col xs={24} md={8}>
          <Card
            style={{ borderRadius: 16 }}
            title={<div className="flex items-center gap-2"><IconExclamationCircle /><span>待审核</span></div>}
            extra={
              <Tag color="orange">{pendingContents.length} 条</Tag>
            }
          >
            {pendingContents.length === 0 ? (
              <div className="text-center py-12">
                <IconCheckCircle className="mb-4" style={{ fontSize: 42, color: "var(--color-success)" }} />
                <p className="font-medium" style={{ color: "var(--text-color-2)" }}>全部审核完毕</p>
                <p className="text-sm mt-1" style={{ color: "var(--text-color-3)" }}>暂无待审核内容</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingContents.map((content) => {
                  const task = tasks.find((t) => t.id === content.taskId);
                  return (
                    <div
                      key={content.id}
                      className="p-4 rounded-xl border cursor-pointer hover:shadow-md transition-all"
                      style={{ borderColor: "var(--border-color)" }}
                      onClick={() => router.push("/review")}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm" style={{ color: "var(--text-color-1)" }}>
                          {task?.productName || "未知商品"}
                        </span>
                        <ScoreBadge score={content.score} size="small" />
                      </div>
                      <p className="text-xs line-clamp-2 m-0" style={{ color: "var(--text-color-3)" }}>
                        {content.text.slice(0, 80)}...
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {task?.config.contentType && <ContentTypeTag type={task.config.contentType} />}
                        {task?.config.platform && <PlatformTag platform={task.config.platform} />}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
