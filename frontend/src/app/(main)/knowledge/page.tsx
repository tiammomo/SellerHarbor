"use client";
import { Card, Button, Tag, Input, Tabs } from "@arco-design/web-react";
import {
  IconStorage,
  IconPlus,
  IconEdit,
  IconDelete,
} from "@arco-design/web-react/icon";
import PageHeader from "@/components/common/PageHeader";

const brandVoices = [
  { id: "1", name: "品牌官方语气", description: "正式、专业、可信，适合详情页和品牌宣传", samples: 12, color: "blue" },
  { id: "2", name: "用户口语化", description: "自然、亲切、生活化，适合评价草稿和社区分享", samples: 28, color: "green" },
  { id: "3", name: "活泼年轻", description: "有趣、有梗、适合小红书和抖音风格", samples: 15, color: "purple" },
  { id: "4", name: "专业测评", description: "客观、数据化、对比明确，适合数码和家电", samples: 8, color: "orange" },
];

const platformRules = [
  { platform: "淘宝", rules: ["避免绝对化用语", "不使用医疗功效宣称", "不提及竞品品牌名"], count: 15 },
  { platform: "小红书", rules: ["口语化表达优先", "避免过度营销感", "可适当使用emoji"], count: 12 },
  { platform: "京东", rules: ["注重参数和数据", "突出品质和服务", "正式但不过度"], count: 10 },
  { platform: "抖音", rules: ["简短有力", "口语化", "引导互动"], count: 8 },
];

const hotPhrases = [
  { phrase: "闭眼入", category: "推荐", usage: 156 },
  { phrase: "回购第N次", category: "复购", usage: 89 },
  { phrase: "真的绝了", category: "感叹", usage: 234 },
  { phrase: "性价比很高", category: "评价", usage: 312 },
  { phrase: "后悔没有早点买", category: "推荐", usage: 67 },
  { phrase: "强烈推荐", category: "推荐", usage: 445 },
  { phrase: "和详情页描述一致", category: "信任", usage: 178 },
  { phrase: "客服态度很好", category: "服务", usage: 95 },
];

export default function KnowledgePage() {
  return (
    <div className="max-w-7xl mx-auto">
      <PageHeader
        title="品牌与话术"
        subtitle="管理品牌语气、平台规则和常用话术模板"
        icon={<IconStorage />}
      />

      <Tabs defaultActiveTab="voice">
        <Tabs.TabPane key="voice" title="品牌语气库">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {brandVoices.map((voice, index) => (
              <Card
                key={voice.id}
                className="hover-lift animate-fade-in"
                style={{ borderRadius: 16, animationDelay: `${index * 80}ms` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-base font-semibold m-0 mb-1" style={{ color: "var(--text-color-1)" }}>
                      {voice.name}
                    </h3>
                    <p className="text-sm m-0" style={{ color: "var(--text-color-3)" }}>
                      {voice.description}
                    </p>
                  </div>
                  <Tag color={voice.color}>{voice.samples} 个样例</Tag>
                </div>
                <div className="flex gap-2">
                  <Button type="text" size="small" icon={<IconEdit />}>编辑</Button>
                  <Button type="text" size="small" icon={<IconDelete />}>删除</Button>
                </div>
              </Card>
            ))}
            <Card
              className="hover-lift cursor-pointer animate-fade-in"
              style={{ borderRadius: 16, animationDelay: `${brandVoices.length * 80}ms`, borderStyle: "dashed" }}
            >
              <div className="flex flex-col items-center justify-center py-8">
                <IconPlus style={{ fontSize: 32, color: "var(--text-color-4)" }} />
                <span className="text-sm mt-2" style={{ color: "var(--text-color-3)" }}>添加品牌语气</span>
              </div>
            </Card>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="rules" title="平台规则">
          <div className="space-y-4 mt-4">
            {platformRules.map((rule, index) => (
              <Card
                key={rule.platform}
                className="hover-lift animate-fade-in"
                style={{ borderRadius: 16, animationDelay: `${index * 80}ms` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-base font-semibold m-0 mb-1" style={{ color: "var(--text-color-1)" }}>
                      {rule.platform}
                    </h3>
                    <span className="text-xs" style={{ color: "var(--text-color-3)" }}>{rule.count} 条规则</span>
                  </div>
                  <Button type="text" size="small" icon={<IconEdit />}>编辑规则</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {rule.rules.map((r) => (
                    <Tag key={r} color="orange" style={{ borderRadius: 8 }}>{r}</Tag>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="phrases" title="热门话术">
          <Card className="mt-4" style={{ borderRadius: 16 }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold m-0" style={{ color: "var(--text-color-1)" }}>
                高频好评话术
              </h3>
              <Button type="primary" size="small" icon={<IconPlus />}>添加话术</Button>
            </div>
            <div className="space-y-3">
              {hotPhrases.map((item, index) => (
                <div
                  key={item.phrase}
                  className="flex items-center justify-between p-3 rounded-xl animate-fade-in"
                  style={{
                    backgroundColor: "var(--color-fill-1)",
                    animationDelay: `${index * 40}ms`,
                  }}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium" style={{ color: "var(--text-color-1)" }}>
                      「{item.phrase}」
                    </span>
                    <Tag style={{ borderRadius: 8, fontSize: 12 }}>{item.category}</Tag>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs" style={{ color: "var(--text-color-3)" }}>
                      使用 {item.usage} 次
                    </span>
                    <Button type="text" size="small" icon={<IconEdit />} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}
