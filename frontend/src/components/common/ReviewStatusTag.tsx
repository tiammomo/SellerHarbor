"use client";
import { Tag } from "@arco-design/web-react";

interface ReviewStatusTagProps {
  status: string;
}

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: "待审核", color: "orange" },
  approved: { label: "已通过", color: "green" },
  rejected: { label: "已驳回", color: "red" },
  rewriting: { label: "重写中", color: "blue" },
};

export default function ReviewStatusTag({ status }: ReviewStatusTagProps) {
  const meta = statusMap[status] || { label: status, color: "gray" };
  return (
    <Tag color={meta.color} style={{ borderRadius: 8 }}>
      {meta.label}
    </Tag>
  );
}
