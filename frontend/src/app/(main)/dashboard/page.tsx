"use client";
import { useMemo, type ReactNode } from "react";
import { Card, Grid, Button, Tag } from "@arco-design/web-react";
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
  IconRefresh,
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
  const { tasks, contents, dashboardStats, businessOverview, commerceOverview, loading, initialized, error, refreshAll } = useDataStore();

  const pendingContents = useMemo(() => contents.filter((c) => c.reviewStatus === "pending"), [contents]);
  const recentContents = useMemo(() => [...contents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 5), [contents]);
  const scoreDistribution = useMemo(() => ({
    excellent: contents.filter((content) => content.score >= 85).length,
    good: contents.filter((content) => content.score >= 70 && content.score < 85).length,
    fair: contents.filter((content) => content.score >= 55 && content.score < 70).length,
    poor: contents.filter((content) => content.score < 55).length,
  }), [contents]);
  const evidenceCoverage = businessOverview.evidenceCoverage ?? { coverageRate: 0, readyProducts: 0 };
  const reviewFunnel = businessOverview.reviewFunnel ?? { exportable: 0, approvalRate: 0 };
  const primaryUseCases = businessOverview.primaryUseCases ?? [];
  const contentMix = businessOverview.contentMix ?? [];
  const recommendedActions = businessOverview.recommendedActions ?? [];
  const commerceKpis = commerceOverview.kpis ?? [];
  const commerceActions = commerceOverview.recommendedActions ?? [];
  const commercePlatforms = commerceOverview.platforms ?? [];
  const commerceWarehouses = commerceOverview.warehouses ?? [];
  const inventoryAlerts = commerceOverview.inventoryAlerts ?? [];
  const hotProducts = commerceOverview.hotProducts ?? [];
  const weeklyGenerations = useMemo(() => normalizeWeeklyGenerations(dashboardStats.weeklyGenerations), [dashboardStats.weeklyGenerations]);
  const hasScoreData = Object.values(scoreDistribution).some((count) => count > 0);
  const hasWeeklyData = weeklyGenerations.some((count) => count > 0);

  const statCards = [
    {
      label: "商品主档",
      value: formatKpiValue(findKpi(commerceKpis, "product_master"), dashboardStats.totalProducts),
      icon: <IconApps />,
      iconColor: "#f97316",
      iconBg: "#f9731618",
      gradient: "primary",
      status: "实时",
    },
    {
      label: "上架就绪率",
      value: formatKpiValue(findKpi(commerceKpis, "listing_readiness"), "0%"),
      icon: <IconCheckCircle />,
      iconColor: "#10b981",
      iconBg: "#10b98118",
      gradient: "success",
      status: "实时",
    },
    {
      label: "库存健康率",
      value: formatKpiValue(findKpi(commerceKpis, "stock_health"), "0%"),
      icon: <IconStorage />,
      iconColor: "#3b82f6",
      iconBg: "#3b82f618",
      gradient: "info",
      status: "实时",
    },
    {
      label: "热款追踪",
      value: formatKpiValue(findKpi(commerceKpis, "hot_products"), 0),
      icon: <IconArrowRise />,
      iconColor: "#f59e0b",
      iconBg: "#f59e0b18",
      gradient: "warning",
      status: "实时",
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
        data: weeklyGenerations,
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
          { value: scoreDistribution.excellent, name: "优秀 (85+)", itemStyle: { color: "#10b981" } },
          { value: scoreDistribution.good, name: "良好 (70-84)", itemStyle: { color: "#3b82f6" } },
          { value: scoreDistribution.fair, name: "一般 (55-69)", itemStyle: { color: "#f59e0b" } },
          { value: scoreDistribution.poor, name: "较差 (<55)", itemStyle: { color: "#ef4444" } },
        ],
      },
    ],
  };

  if (loading && !initialized) {
    return (
      <div className="max-w-7xl mx-auto animate-fade-in">
        <DashboardSkeleton />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      {error && (
        <div
          className="mb-4 flex flex-col gap-3 rounded-xl border px-4 py-3 md:flex-row md:items-center md:justify-between"
          style={{ borderColor: "#ef444433", backgroundColor: "#ef44440f" }}
        >
          <div className="flex items-start gap-3">
            <IconExclamationCircle className="mt-0.5 shrink-0" style={{ color: "var(--color-danger)", fontSize: 18 }} />
            <div>
              <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>数据加载失败，当前显示本地兜底数据</div>
              <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{error}</div>
            </div>
          </div>
          <Button size="small" icon={<IconRefresh />} loading={loading} onClick={() => void refreshAll()}>
            重新加载
          </Button>
        </div>
      )}

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
                    backgroundColor: "#0f172a0d",
                    color: "var(--text-color-3)",
                  }}
                >
                  {card.status}
                </div>
              </div>
              <div className="text-sm mb-1" style={{ color: "var(--text-color-3)" }}>{card.label}</div>
              <div className="text-2xl font-bold" style={{ color: "var(--text-color-1)" }}>{card.value}</div>
            </div>
          </Col>
        ))}
      </Row>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)] gap-4 mb-6 items-stretch">
        <Card
          className="h-full"
          style={{ borderRadius: 16 }}
          title={<div className="flex items-center gap-2"><IconDashboard /><span>{commerceOverview.positioning}</span></div>}
        >
          <div className="flex flex-wrap gap-2 mb-4">
            {commerceOverview.operatingFocus.map((focus) => (
              <Tag key={focus} color="arcoblue">{focus}</Tag>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {commercePlatforms.map((platform) => (
              <div key={platform.platform} className="rounded-xl p-4" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold" style={{ color: "var(--text-color-1)" }}>{platform.label}</div>
                    <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{platform.priorityAction}</div>
                  </div>
                  <div className="text-2xl font-bold" style={{ color: platform.readinessRate >= 70 ? "var(--color-success)" : "var(--color-warning)" }}>
                    {platform.readinessRate}%
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 mt-4">
                  <MiniMetric label="就绪" value={platform.readyListings} tone="#10b981" />
                  <MiniMetric label="待优化" value={platform.watchListings} tone="#f59e0b" />
                  <MiniMetric label="缺失" value={platform.missingListings} tone="#ef4444" />
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {commerceWarehouses.slice(0, 3).map((warehouse) => (
              <div key={warehouse.key} className="rounded-xl p-4" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="text-sm font-medium truncate" style={{ color: "var(--text-color-1)" }}>{warehouse.name}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{warehouse.country} · {warehouse.platforms.map(platformDisplayName).join(" / ")}</div>
                <div className="flex items-end justify-between mt-4">
                  <div>
                    <div className="text-2xl font-bold" style={{ color: "var(--color-primary)" }}>{warehouse.totalUnits}</div>
                    <div className="text-xs" style={{ color: "var(--text-color-3)" }}>可用库存</div>
                  </div>
                  <Tag color={warehouse.lowStockSkus ? "orange" : "green"}>{warehouse.stockHealthRate}% 健康</Tag>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card
          className="h-full"
          style={{ borderRadius: 16 }}
          title={<div className="flex items-center gap-2"><IconArrowRise /><span>跨境运营动作</span></div>}
        >
          <div className="space-y-3">
            {commerceActions.map((action) => (
              <div key={action.key} className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{action.label}</div>
                    <div className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-color-3)" }}>{action.detail}</div>
                  </div>
                  <Tag color={actionToneColor(action.tone)}>{action.priority}</Tag>
                </div>
                <Button type="text" size="small" className="mt-2" onClick={() => router.push(action.href)}>
                  去处理 <IconRight />
                </Button>
              </div>
            ))}
            {inventoryAlerts.slice(0, 2).map((alert) => (
              <div key={`${alert.productId}-${alert.warehouseKey}`} className="rounded-xl p-3 border" style={{ borderColor: "#f59e0b55", backgroundColor: "#f59e0b0f" }}>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate" style={{ color: "var(--text-color-1)" }}>{alert.productName}</div>
                    <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{alert.sku} · {alert.warehouseName}</div>
                  </div>
                  <Tag color={alert.status === "out_of_stock" ? "red" : "orange"}>{inventoryStatusLabel(alert.status)}</Tag>
                </div>
              </div>
            ))}
            {hotProducts[0] && (
              <div className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate" style={{ color: "var(--text-color-1)" }}>当前热款：{hotProducts[0].productName}</div>
                    <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>近 7 日 {hotProducts[0].weeklySales} 单 · 评分 {hotProducts[0].rating || "-"}</div>
                  </div>
                  <Tag color={heatLevelColor(hotProducts[0].heatLevel)}>{hotProducts[0].heatScore}</Tag>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)] gap-4 mb-6 items-stretch">
          <Card
            className="h-full"
            style={{ borderRadius: 16 }}
            title={<div className="flex items-center gap-2"><IconStorage /><span>{businessOverview.positioning}</span></div>}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <BusinessMetric label="证据覆盖率" value={`${evidenceCoverage.coverageRate}%`} tone="#3b82f6" />
              <BusinessMetric label="就绪商品" value={evidenceCoverage.readyProducts} tone="#10b981" />
              <BusinessMetric label="可导出素材" value={reviewFunnel.exportable} tone="#f97316" />
              <BusinessMetric label="审核通过率" value={`${reviewFunnel.approvalRate}%`} tone="#8b5cf6" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium" style={{ color: "var(--text-color-2)" }}>业务优先场景</span>
                  <Tag color="blue">{primaryUseCases.length} 项</Tag>
                </div>
                <div className="flex flex-wrap gap-2">
                  {primaryUseCases.map((useCase) => (
                    <Tag key={useCase} color="arcoblue">{useCase}</Tag>
                  ))}
                </div>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--color-fill-1)" }}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium" style={{ color: "var(--text-color-2)" }}>素材结构</span>
                  <Tag color="green">{contentMix.length || 0} 类</Tag>
                </div>
                <div className="space-y-2">
                  {contentMix.slice(0, 3).map((item) => (
                    <div key={item.contentType} className="flex items-center gap-2">
                      <span className="w-20 text-xs" style={{ color: "var(--text-color-3)" }}>{item.label}</span>
                      <div className="h-2 flex-1 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-fill-3)" }}>
                        <div className="h-full rounded-full" style={{ width: `${item.share}%`, backgroundColor: "#f97316" }} />
                      </div>
                      <span className="w-10 text-right text-xs" style={{ color: "var(--text-color-3)" }}>{item.count}</span>
                    </div>
                  ))}
                  {contentMix.length === 0 && (
                    <span className="text-sm" style={{ color: "var(--text-color-3)" }}>暂无生成内容</span>
                  )}
                </div>
              </div>
            </div>
          </Card>

          <Card
            className="h-full"
            style={{ borderRadius: 16 }}
            title={<div className="flex items-center gap-2"><IconArrowRise /><span>下一步动作</span></div>}
          >
            {recommendedActions.length === 0 ? (
              <InlineEmptyState
                icon={<IconCheckCircle />}
                title="暂无紧急动作"
                description="数据准备完成后，这里会自动给出下一步运营建议。"
                minHeight={220}
              />
            ) : (
              <div className="space-y-3">
                {recommendedActions.map((action) => (
                  <div key={action.key} className="rounded-xl p-3" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{action.label}</div>
                        <div className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-color-3)" }}>{action.detail}</div>
                      </div>
                      <Tag color={actionToneColor(action.tone)}>{action.priority}</Tag>
                    </div>
                    <Button type="text" size="small" className="mt-2" onClick={() => router.push(action.href)}>
                      去处理 <IconRight />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
      </div>

      {/* Quality overview + Chart */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6 items-stretch">
          <Card className="h-full" style={{ borderRadius: 16 }} title={<div className="flex items-center gap-2"><IconDashboard /><span>质量概览</span></div>}>
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
            {hasScoreData ? (
              <ReactECharts option={scoreDistOption} style={{ height: 240 }} notMerge lazyUpdate />
            ) : (
              <ChartEmptyState title="暂无评分分布" description="生成并审核内容后，会在这里展示质量结构。" height={240} />
            )}
          </Card>

          <Card className="h-full" style={{ borderRadius: 16 }} title={<div className="flex items-center gap-2"><IconStorage /><span>本周生成趋势</span></div>}>
            {hasWeeklyData ? (
              <ReactECharts option={chartOption} style={{ height: 320 }} notMerge lazyUpdate />
            ) : (
              <ChartEmptyState title="暂无本周生成数据" description="开始生成内容后，趋势图会自动更新。" height={320} />
            )}
          </Card>
      </div>

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
            {recentContents.length === 0 ? (
              <InlineEmptyState
                icon={<IconEdit />}
                title="暂无生成内容"
                description="完成一次内容生成后，最近记录会显示在这里。"
                actionText="去生成"
                minHeight={260}
                onAction={() => router.push("/generate")}
              />
            ) : (
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
            )}
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

function normalizeWeeklyGenerations(values?: number[]) {
  const source = Array.isArray(values) ? values : [];
  const normalized = source.filter((value) => Number.isFinite(value)).slice(-7);
  return [...Array(Math.max(0, 7 - normalized.length)).fill(0), ...normalized];
}

function findKpi(kpis: Array<{ key: string; value: number | string; unit?: string }>, key: string) {
  return kpis.find((item) => item.key === key);
}

function formatKpiValue(kpi: { value: number | string; unit?: string } | undefined, fallback: number | string) {
  if (!kpi) return fallback;
  return `${kpi.value}${kpi.unit || ""}`;
}

function BusinessMetric({ label, value, tone }: { label: string; value: number | string; tone: string }) {
  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <div className="text-xs" style={{ color: "var(--text-color-3)" }}>{label}</div>
      <div className="text-2xl font-bold mt-2" style={{ color: tone }}>{value}</div>
    </div>
  );
}

function MiniMetric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="rounded-lg px-2 py-2 text-center" style={{ backgroundColor: "var(--color-fill-2)" }}>
      <div className="text-lg font-bold" style={{ color: tone }}>{value}</div>
      <div className="text-xs" style={{ color: "var(--text-color-3)" }}>{label}</div>
    </div>
  );
}

function platformDisplayName(platform: string) {
  if (platform === "temu") return "Temu";
  if (platform === "tiktok_shop") return "TikTok Shop";
  return platform;
}

function inventoryStatusLabel(status: "healthy" | "low_stock" | "out_of_stock") {
  if (status === "out_of_stock") return "断货";
  if (status === "low_stock") return "低库存";
  return "健康";
}

function heatLevelColor(level: "hot" | "rising" | "steady" | "needs_attention") {
  if (level === "hot") return "red";
  if (level === "rising") return "orange";
  if (level === "steady") return "green";
  return "gray";
}

function ChartEmptyState({ title, description, height }: { title: string; description: string; height: number }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl px-6 text-center"
      style={{ minHeight: height, backgroundColor: "var(--color-fill-1)" }}
    >
      <IconDashboard className="mb-3" style={{ fontSize: 34, color: "var(--text-color-4)" }} />
      <div className="text-sm font-medium" style={{ color: "var(--text-color-2)" }}>{title}</div>
      <div className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-color-3)" }}>{description}</div>
    </div>
  );
}

function InlineEmptyState({
  icon,
  title,
  description,
  actionText,
  minHeight,
  onAction,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  actionText?: string;
  minHeight: number;
  onAction?: () => void;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl px-6 py-8 text-center"
      style={{ minHeight, backgroundColor: "var(--color-fill-1)" }}
    >
      <div className="mb-3 text-3xl" style={{ color: "var(--text-color-4)" }}>{icon}</div>
      <div className="text-sm font-medium" style={{ color: "var(--text-color-2)" }}>{title}</div>
      <div className="text-xs mt-1 max-w-sm leading-relaxed" style={{ color: "var(--text-color-3)" }}>{description}</div>
      {actionText && onAction && (
        <Button className="mt-4" size="small" type="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <SkeletonBlock key={index} className="h-32" />
        ))}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(360px,1fr)] gap-4">
        <SkeletonBlock className="h-64" />
        <SkeletonBlock className="h-64" />
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SkeletonBlock className="h-96" />
        <SkeletonBlock className="h-96" />
      </div>
    </div>
  );
}

function SkeletonBlock({ className }: { className: string }) {
  return (
    <div
      className={`animate-pulse rounded-2xl border ${className}`}
      style={{ borderColor: "var(--border-color)", backgroundColor: "var(--color-fill-1)" }}
    />
  );
}

function actionToneColor(tone: "primary" | "warning" | "success" | "neutral") {
  if (tone === "primary") return "arcoblue";
  if (tone === "warning") return "orange";
  if (tone === "success") return "green";
  return "gray";
}
