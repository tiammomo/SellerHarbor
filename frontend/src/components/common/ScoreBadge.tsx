"use client";
import { Tag } from "@arco-design/web-react";

interface ScoreBadgeProps {
  score: number;
  size?: "small" | "medium" | "large";
}

export default function ScoreBadge({ score, size = "medium" }: ScoreBadgeProps) {
  const getScoreClass = (s: number) => {
    if (s >= 85) return "score-excellent";
    if (s >= 70) return "score-good";
    if (s >= 55) return "score-medium";
    return "score-poor";
  };

  const getScoreLabel = (s: number) => {
    if (s >= 85) return "优秀";
    if (s >= 70) return "良好";
    if (s >= 55) return "一般";
    return "较差";
  };

  const sizeStyles = {
    small: { fontSize: 12, padding: "1px 8px", borderRadius: 8 },
    medium: { fontSize: 13, padding: "2px 10px", borderRadius: 10 },
    large: { fontSize: 16, padding: "4px 14px", borderRadius: 12 },
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold ${getScoreClass(score)}`}
      style={sizeStyles[size]}
    >
      {score}
      <span className="text-xs font-normal opacity-80">{getScoreLabel(score)}</span>
    </span>
  );
}
