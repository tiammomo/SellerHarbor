"use client";
import { Tag } from "@arco-design/web-react";
import {
  contentTypeLabels,
  platformLabels,
  toneLabels,
  lengthLabels,
  personaLabels,
  type ContentType,
  type Platform,
  type Tone,
  type Length,
  type Persona,
} from "@/lib/types";

const contentTypeColors: Record<ContentType, string> = {
  review_draft: "blue",
  experience_copy: "green",
  recommendation: "purple",
  review_invitation: "orange",
  share_guide: "cyan",
  cs_followup: "lime",
  detail_page: "magenta",
};

const platformColors: Record<Platform, string> = {
  taobao: "orange",
  tmall: "red",
  jd: "red",
  pdd: "orange",
  douyin: "purple",
  xiaohongshu: "magenta",
  independent: "blue",
  temu: "orange",
  tiktok_shop: "purple",
};

export function ContentTypeTag({ type }: { type: ContentType }) {
  return <Tag color={contentTypeColors[type] || "gray"}>{contentTypeLabels[type] || type}</Tag>;
}

export function PlatformTag({ platform }: { platform: Platform }) {
  return <Tag color={platformColors[platform] || "gray"}>{platformLabels[platform] || platform}</Tag>;
}

export function ToneTag({ tone }: { tone: Tone }) {
  return <Tag>{toneLabels[tone] || tone}</Tag>;
}

export function LengthTag({ length }: { length: Length }) {
  return <Tag>{lengthLabels[length] || length}</Tag>;
}

export function PersonaTag({ persona }: { persona: Persona }) {
  return <Tag>{personaLabels[persona] || persona}</Tag>;
}
