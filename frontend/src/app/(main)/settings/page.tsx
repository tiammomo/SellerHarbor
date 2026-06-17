"use client";
import { useEffect, useState } from "react";
import { Card, Button, Form, Input, Select, Switch, Tabs, Message, Tag } from "@arco-design/web-react";
import {
  IconCheckCircle,
  IconExclamationCircle,
  IconRefresh,
  IconSettings,
  IconUser,
  IconSafe,
  IconStorage,
  IconApps,
} from "@arco-design/web-react/icon";
import { apiClient } from "@/lib/api/client";
import PageHeader from "@/components/common/PageHeader";
import type { LlmHealth, StoreRegistry, SystemReadiness, TemuIntegrationStatus } from "@/lib/types";

const FormItem = Form.Item;

export default function SettingsPage() {
  const [llmHealth, setLlmHealth] = useState<LlmHealth | null>(null);
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [temuStatus, setTemuStatus] = useState<TemuIntegrationStatus | null>(null);
  const [storeRegistry, setStoreRegistry] = useState<StoreRegistry | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  const refreshHealth = async () => {
    setHealthLoading(true);
    try {
      const [nextLlmHealth, nextReadiness, nextTemuStatus, nextStoreRegistry] = await Promise.all([
        apiClient.getLlmHealth(),
        apiClient.getReadiness(),
        apiClient.getTemuIntegrationStatus(),
        apiClient.getStoreRegistry(),
      ]);
      setLlmHealth(nextLlmHealth);
      setReadiness(nextReadiness);
      setTemuStatus(nextTemuStatus);
      setStoreRegistry(nextStoreRegistry);
    } catch (error) {
      Message.error(error instanceof Error ? error.message : "系统状态加载失败");
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    void refreshHealth();
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader
        title="系统设置"
        subtitle="配置系统参数、模型偏好和安全策略"
        icon={<IconSettings />}
      />

      <Tabs defaultActiveTab="general" tabPosition="top">
        <Tabs.TabPane key="general" title={<span className="flex items-center gap-1"><IconSettings /> 基本设置</span>}>
          <Card style={{ borderRadius: 16 }} className="mt-4">
            <Form layout="vertical">
              <h3 className="text-base font-semibold mb-4" style={{ color: "var(--text-color-1)" }}>团队信息</h3>
              <FormItem label="团队名称">
                <Input defaultValue="SellerHarbor 默认团队" />
              </FormItem>
              <FormItem label="默认生成语言">
                <Select defaultValue="zh">
                  <Select.Option value="zh">中文</Select.Option>
                  <Select.Option value="en">English</Select.Option>
                </Select>
              </FormItem>

              <h3 className="text-base font-semibold mb-4 mt-6" style={{ color: "var(--text-color-1)" }}>生成默认值</h3>
              <div className="grid grid-cols-2 gap-4">
                <FormItem label="默认平台">
                  <Select defaultValue="taobao">
                    <Select.Option value="taobao">淘宝</Select.Option>
                    <Select.Option value="xiaohongshu">小红书</Select.Option>
                    <Select.Option value="jd">京东</Select.Option>
                  </Select>
                </FormItem>
                <FormItem label="默认语气">
                  <Select defaultValue="natural">
                    <Select.Option value="natural">自然</Select.Option>
                    <Select.Option value="sincere">真诚</Select.Option>
                    <Select.Option value="professional">专业</Select.Option>
                  </Select>
                </FormItem>
                <FormItem label="默认生成数量">
                  <Select defaultValue="3">
                    <Select.Option value="1">1 条</Select.Option>
                    <Select.Option value="3">3 条</Select.Option>
                    <Select.Option value="5">5 条</Select.Option>
                    <Select.Option value="10">10 条</Select.Option>
                  </Select>
                </FormItem>
                <FormItem label="默认长度">
                  <Select defaultValue="medium">
                    <Select.Option value="short">短句</Select.Option>
                    <Select.Option value="medium">中等</Select.Option>
                    <Select.Option value="long">长段</Select.Option>
                  </Select>
                </FormItem>
              </div>

              <div className="flex justify-end mt-4">
                <Button type="primary" onClick={() => Message.success("设置已保存（演示）")}>保存设置</Button>
              </div>
            </Form>
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane key="model" title={<span className="flex items-center gap-1"><IconSafe /> 模型配置</span>}>
          <Card style={{ borderRadius: 16 }} className="mt-4">
            <div className="flex items-center justify-between gap-3 mb-5">
              <div>
                <h3 className="text-base font-semibold" style={{ color: "var(--text-color-1)" }}>运行状态</h3>
                <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>
                  {readiness ? `环境: ${readiness.environment} · 更新时间: ${new Date(readiness.time).toLocaleString()}` : "正在读取系统状态"}
                </div>
              </div>
              <Button icon={<IconRefresh />} loading={healthLoading} onClick={refreshHealth}>
                刷新
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
              <StatusPanel label="系统" status={readiness?.status} detail={readiness?.status ? readiness.status : "loading"} />
              <StatusPanel label="LLM 网关" status={llmHealth?.status} detail={llmHealth?.detail || "loading"} />
              <StatusPanel
                label="模型"
                status={llmHealth?.configured ? "healthy" : "unconfigured"}
                detail={llmHealth?.model || "未配置"}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
              <ConfigLine label="Provider" value={llmHealth?.provider || "-"} />
              <ConfigLine label="Base URL" value={llmHealth?.baseUrl || "-"} />
              <ConfigLine label="Latency" value={llmHealth?.latencyMs != null ? `${llmHealth.latencyMs} ms` : "-"} />
              <ConfigLine label="Configured" value={llmHealth?.configured ? "true" : "false"} />
            </div>

            <div className="space-y-2">
              {(readiness?.checks || []).map((check) => (
                <div
                  key={check.key}
                  className="flex items-start justify-between gap-4 p-3 rounded-xl"
                  style={{ backgroundColor: "var(--color-fill-1)" }}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {check.status === "healthy" ? (
                        <IconCheckCircle style={{ color: "var(--color-success)" }} />
                      ) : (
                        <IconExclamationCircle style={{ color: check.severity === "critical" ? "var(--color-danger)" : "var(--color-warning)" }} />
                      )}
                      <span className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{check.label}</span>
                    </div>
                    <div className="text-xs break-words" style={{ color: "var(--text-color-3)" }}>{check.detail}</div>
                  </div>
                  <Tag color={statusColor(check.status)}>{check.status}</Tag>
                </div>
              ))}
            </div>
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane key="integrations" title={<span className="flex items-center gap-1"><IconStorage /> 平台接入</span>}>
          <div className="space-y-4 mt-4">
            <Card style={{ borderRadius: 16 }}>
              <div className="flex items-start justify-between gap-3 mb-5">
                <div>
                  <h3 className="text-base font-semibold" style={{ color: "var(--text-color-1)" }}>店铺管理预留</h3>
                  <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>
                    当前按单店铺运行，商品主档保留在租户层，平台 Listing 和授权后续按 storeId 关联
                  </div>
                </div>
                <Button icon={<IconRefresh />} loading={healthLoading} onClick={refreshHealth}>
                  刷新
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
                <StatusPanel
                  label="运行模式"
                  status={storeRegistry?.multiStoreEnabled ? "ready" : "planned"}
                  detail={storeRegistry?.mode || "loading"}
                />
                <ConfigLine label="Default Store" value={storeRegistry?.defaultStoreId || "-"} />
                <ConfigLine label="Tenant" value={storeRegistry?.tenantId || "-"} />
              </div>

              <div className="space-y-3 mb-5">
                {(storeRegistry?.stores || []).map((store) => (
                  <div key={store.id} className="p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <IconApps style={{ color: "var(--color-primary-6)" }} />
                          <span className="text-sm font-semibold" style={{ color: "var(--text-color-1)" }}>{store.name}</span>
                          <Tag color="arcoblue">{store.platformLabel}</Tag>
                          {store.isDefault && <Tag color="green">default</Tag>}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs" style={{ color: "var(--text-color-3)" }}>
                          <span>Store ID: {store.id}</span>
                          <span>Region: {store.region}</span>
                          <span>Warehouse: {store.defaultWarehouse}</span>
                          <span>Credentials: {store.credentialScope}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 md:justify-end">
                        <Tag color={statusColor(store.status)}>{store.status}</Tag>
                        <Tag color={statusColor(store.connectionStatus)}>{store.connectionStatus}</Tag>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {store.capabilities.map((capability) => (
                        <Tag key={capability.key} color={statusColor(capability.status)}>
                          {capability.label}: {capability.status}
                        </Tag>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>后续扩展槽</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
                {(storeRegistry?.expansionSlots || []).map((slot) => (
                  <div key={slot.key} className="p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="min-w-0">
                        <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{slot.label}</div>
                        <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{slot.detail}</div>
                      </div>
                      <Tag color={statusColor(slot.status)}>{slot.status}</Tag>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {slot.requiredEnvVars.slice(0, 3).map((envVar) => (
                        <Tag key={envVar} color="arcoblue">{envVar}</Tag>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>数据模型边界</h4>
              <div className="space-y-2">
                {(storeRegistry?.dataBoundaries || []).map((item) => (
                  <div key={item.key} className="p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                    <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{item.label}</div>
                    <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{item.currentState}</div>
                    <div className="text-xs mt-1 break-words" style={{ color: "var(--text-color-3)" }}>{item.nextSchema}</div>
                  </div>
                ))}
              </div>
            </Card>

            <Card style={{ borderRadius: 16 }}>
              <div className="flex items-start justify-between gap-3 mb-5">
                <div>
                  <h3 className="text-base font-semibold" style={{ color: "var(--text-color-1)" }}>Temu 只读同步准备</h3>
                  <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>
                    先同步商品、订单、履约和库存信号；价格、库存、Listing 写回默认保持禁用
                  </div>
                </div>
                <Button icon={<IconRefresh />} loading={healthLoading} onClick={refreshHealth}>
                  刷新
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
                <StatusPanel label="连接状态" status={temuStatus?.configured ? "healthy" : "skipped"} detail={temuStatus?.readiness || "loading"} />
                <ConfigLine label="Region" value={temuStatus?.region || "-"} />
                <ConfigLine label="Sandbox" value={temuStatus ? String(temuStatus.sandbox) : "-"} />
              </div>

              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>需要你稍后提供</h4>
              <div className="space-y-2 mb-5">
                {(temuStatus?.requirements || []).map((item) => (
                  <div
                    key={item.key}
                    className="p-3 rounded-xl"
                    style={{ backgroundColor: "var(--color-fill-1)" }}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{item.label}</div>
                        <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{item.detail}</div>
                      </div>
                      <Tag color={statusColor(item.status)}>{item.status}</Tag>
                    </div>
                    {item.envVars.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {item.envVars.map((envVar) => (
                          <Tag key={envVar} color="arcoblue">{envVar}</Tag>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>能力推进顺序</h4>
              <div className="space-y-2 mb-5">
                {(temuStatus?.capabilities || []).map((item) => (
                  <div
                    key={item.key}
                    className="flex items-start justify-between gap-3 p-3 rounded-xl"
                    style={{ backgroundColor: "var(--color-fill-1)" }}
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{item.label}</span>
                        <Tag color={item.mode === "write" ? "red" : item.mode === "event" ? "orange" : "green"}>{item.mode}</Tag>
                      </div>
                      <div className="text-xs" style={{ color: "var(--text-color-3)" }}>{item.detail}</div>
                      <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>权限: {item.requiredPermission}</div>
                    </div>
                    <Tag color={statusColor(item.status)}>{item.status}</Tag>
                  </div>
                ))}
              </div>

              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text-color-1)" }}>下一步动作</h4>
              <div className="space-y-2">
                {(temuStatus?.nextActions || []).map((action) => (
                  <div key={action} className="text-sm p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)", color: "var(--text-color-2)" }}>
                    {action}
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="safety" title={<span className="flex items-center gap-1"><IconSafe /> 安全策略</span>}>
          <Card style={{ borderRadius: 16 }} className="mt-4">
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-semibold mb-4" style={{ color: "var(--text-color-1)" }}>内容安全</h3>
                <div className="space-y-4">
                  {[
                    { label: "事实约束检查", desc: "生成内容必须基于已确认事实，不允许编造", defaultChecked: true },
                    { label: "夸大宣传检测", desc: "自动检测并拦截夸大、绝对化表达", defaultChecked: true },
                    { label: "敏感词过滤", desc: "过滤医疗、金融等敏感领域宣称", defaultChecked: true },
                    { label: "冒充风险检测", desc: "检测是否模拟真实消费者身份", defaultChecked: true },
                    { label: "重复内容检测", desc: "检测并避免批量生成高度相似内容", defaultChecked: true },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
                      <div>
                        <div className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>{item.label}</div>
                        <div className="text-xs mt-1" style={{ color: "var(--text-color-3)" }}>{item.desc}</div>
                      </div>
                      <Switch defaultChecked={item.defaultChecked} />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-base font-semibold mb-4" style={{ color: "var(--text-color-1)" }}>
                  风险拦截阈值
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <FormItem label="最低质量分">
                    <Select defaultValue="60">
                      <Select.Option value="50">50 分</Select.Option>
                      <Select.Option value="60">60 分（推荐）</Select.Option>
                      <Select.Option value="70">70 分</Select.Option>
                      <Select.Option value="80">80 分（严格）</Select.Option>
                    </Select>
                  </FormItem>
                  <FormItem label="最大重复度">
                    <Select defaultValue="20">
                      <Select.Option value="10">10%</Select.Option>
                      <Select.Option value="20">20%（推荐）</Select.Option>
                      <Select.Option value="30">30%</Select.Option>
                    </Select>
                  </FormItem>
                </div>
              </div>

              <div className="flex justify-end">
                <Button type="primary" onClick={() => Message.success("安全策略已保存（演示）")}>保存策略</Button>
              </div>
            </div>
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane key="account" title={<span className="flex items-center gap-1"><IconUser /> 账户信息</span>}>
          <Card style={{ borderRadius: 16 }} className="mt-4">
            <Form layout="vertical">
              <FormItem label="昵称">
                <Input defaultValue="运营人员" />
              </FormItem>
              <FormItem label="邮箱">
                <Input defaultValue="admin@sellerharbor.local" />
              </FormItem>
              <FormItem label="角色">
                <Tag color="blue" style={{ borderRadius: 8, padding: "4px 12px" }}>管理员</Tag>
              </FormItem>

              <div className="flex justify-end mt-4">
                <Button type="primary" onClick={() => Message.success("账户信息已更新（演示）")}>更新信息</Button>
              </div>
            </Form>
          </Card>
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}

function StatusPanel({ label, status, detail }: { label: string; status?: string; detail: string }) {
  return (
    <div className="p-4 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs" style={{ color: "var(--text-color-3)" }}>{label}</span>
        <Tag color={statusColor(status)}>{status || "loading"}</Tag>
      </div>
      <div className="text-sm font-medium break-words" style={{ color: "var(--text-color-1)" }}>{detail}</div>
    </div>
  );
}

function ConfigLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 p-3 rounded-xl" style={{ backgroundColor: "var(--color-fill-1)" }}>
      <span className="text-xs shrink-0" style={{ color: "var(--text-color-3)" }}>{label}</span>
      <span className="text-sm text-right break-all" style={{ color: "var(--text-color-1)" }}>{value}</span>
    </div>
  );
}

function statusColor(status?: string) {
  if (status === "healthy" || status === "ready" || status === "active") return "green";
  if (
    status === "degraded" ||
    status === "skipped" ||
    status === "enabled" ||
    status === "manual" ||
    status === "planned" ||
    status === "needs_permission" ||
    status === "needs_credentials" ||
    status === "needs_authorization" ||
    status === "ready_for_config"
  ) return "orange";
  if (status === "unavailable" || status === "unconfigured" || status === "missing" || status === "blocked" || status === "disabled") return "red";
  return "gray";
}
