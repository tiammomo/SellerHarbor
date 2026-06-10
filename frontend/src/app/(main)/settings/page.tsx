"use client";
import { Card, Button, Form, Input, Select, Switch, Tabs, Message, Tag } from "@arco-design/web-react";
import {
  IconSettings,
  IconUser,
  IconSafe,
  IconNotification,
  IconStorage,
} from "@arco-design/web-react/icon";
import PageHeader from "@/components/common/PageHeader";

const FormItem = Form.Item;

export default function SettingsPage() {
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
                <Input defaultValue="ReviewPilot 默认团队" />
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
            <Form layout="vertical">
              <h3 className="text-base font-semibold mb-4" style={{ color: "var(--text-color-1)" }}>LLM 配置</h3>
              <FormItem label="模型提供商">
                <Select defaultValue="openai">
                  <Select.Option value="openai">OpenAI</Select.Option>
                  <Select.Option value="anthropic">Anthropic</Select.Option>
                  <Select.Option value="deepseek">DeepSeek</Select.Option>
                  <Select.Option value="qwen">通义千问</Select.Option>
                </Select>
              </FormItem>
              <FormItem label="API Key">
                <Input.Password placeholder="sk-..." />
              </FormItem>
              <FormItem label="模型名称">
                <Input defaultValue="gpt-4o" placeholder="例: gpt-4o, claude-3.5-sonnet" />
              </FormItem>
              <FormItem label="Temperature">
                <Select defaultValue="0.7">
                  <Select.Option value="0.3">0.3 (更稳定)</Select.Option>
                  <Select.Option value="0.5">0.5</Select.Option>
                  <Select.Option value="0.7">0.7 (推荐)</Select.Option>
                  <Select.Option value="0.9">0.9 (更创意)</Select.Option>
                </Select>
              </FormItem>

              <div className="flex justify-end mt-4">
                <Button type="primary" onClick={() => Message.success("模型配置已保存（演示）")}>保存配置</Button>
              </div>
            </Form>
          </Card>
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
                <Input defaultValue="admin@reviewpilot.com" />
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
