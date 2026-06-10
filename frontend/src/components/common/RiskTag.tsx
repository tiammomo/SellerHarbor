"use client";
import { Tag } from "@arco-design/web-react";

interface RiskTagProps {
  flags: string[];
}

const riskLabels: Record<string, { label: string; color: string }> = {
  fabricated_experience: { label: "捏造体验", color: "red" },
  unsupported_claim: { label: "无依据声明", color: "orange" },
  prohibited_claim: { label: "违禁表达", color: "red" },
  medical_or_financial_claim: { label: "医疗/金融宣称", color: "red" },
  platform_policy_risk: { label: "平台违规", color: "orange" },
  spam_pattern: { label: "灌水嫌疑", color: "orange" },
  impersonation_risk: { label: "冒充风险", color: "red" },
  mild_exaggeration: { label: "轻微夸大", color: "gold" },
  minor_concern: { label: "小问题", color: "gold" },
  forbidden_claim: { label: "命中禁用词", color: "red" },
  platform_sensitive_claim: { label: "平台敏感词", color: "orange" },
  high_repetition_risk: { label: "重复风险高", color: "orange" },
  high_exaggeration_risk: { label: "夸大风险高", color: "red" },
  low_quality_score: { label: "质量偏低", color: "gold" },
  missing_feedback_context: { label: "缺少反馈依据", color: "orange" },
  merchant_voice_review_risk: { label: "商家口吻风险", color: "orange" },
  safe_alternative_generated: { label: "安全替代", color: "blue" },
};

export default function RiskTag({ flags }: RiskTagProps) {
  if (!flags || flags.length === 0) {
    return (
      <Tag color="green" style={{ borderRadius: 8 }}>
        ✓ 无风险
      </Tag>
    );
  }

  return (
    <div className="flex flex-wrap gap-1">
      {flags.map((flag) => {
        const meta = riskLabels[flag] || { label: flag, color: "gray" };
        return (
          <Tag key={flag} color={meta.color} style={{ borderRadius: 8 }}>
            ⚠ {meta.label}
          </Tag>
        );
      })}
    </div>
  );
}
