"use client";
import { Progress } from "@arco-design/web-react";

interface QualityBarProps {
  label: string;
  value: number;
  max?: number;
}

export default function QualityBar({ label, value, max = 100 }: QualityBarProps) {
  const percent = Math.round((value / max) * 100);
  const color = percent >= 80 ? "#10b981" : percent >= 60 ? "#3b82f6" : percent >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs w-20 shrink-0 truncate" style={{ color: "var(--text-color-3)" }}>
        {label}
      </span>
      <div className="flex-1">
        <Progress
          percent={percent}
          color={color}
          showText={false}
          size="small"
        />
      </div>
      <span className="text-xs font-medium w-8 text-right" style={{ color: "var(--text-color-2)" }}>
        {value}
      </span>
    </div>
  );
}
