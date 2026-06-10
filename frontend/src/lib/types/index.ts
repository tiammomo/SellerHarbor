// Product types
export interface Product {
  id: string;
  name: string;
  category: string;
  attributes: Record<string, string>;
  sellingPoints: string[];
  targetAudiences: string[];
  usageScenarios: string[];
  forbiddenClaims: string[];
  brandVoiceId?: string;
  createdAt: string;
  updatedAt: string;
}

// Feedback types
export interface Feedback {
  id: string;
  productId: string;
  productName?: string;
  sourceType: "customer_review" | "cs_summary" | "after_sales" | "authorized";
  sourceSummary: string;
  confirmedFacts: string[];
  subjectiveOpinions: string[];
  consentStatus: "confirmed" | "pending" | "not_required";
  createdAt: string;
}

// Generation config
export type ContentType =
  | "review_draft"
  | "experience_copy"
  | "recommendation"
  | "review_invitation"
  | "share_guide"
  | "cs_followup"
  | "detail_page";

export type Platform =
  | "taobao"
  | "tmall"
  | "jd"
  | "pdd"
  | "douyin"
  | "xiaohongshu"
  | "independent";

export type Tone = "natural" | "sincere" | "lively" | "professional" | "brief" | "detailed";
export type Length = "short" | "medium" | "long";
export type Persona = "first_person" | "third_person" | "merchant";

export interface GenerationConfig {
  productId: string;
  feedbackId?: string;
  contentType: ContentType;
  platform: Platform;
  merchantType?: string;
  tone: Tone;
  length: Length;
  persona: Persona;
  scenario?: string;
  count: number;
}

export interface PlatformRule {
  platform: Platform;
  merchantType: string;
  displayName: string;
  objective: string;
  voice: string;
  structure: string[];
  positiveSignals: string[];
  avoidClaims: string[];
  riskTerms: string[];
  maxShortRunes: number;
  requireExperienceEvidence: boolean;
  merchantVoiceReviewRisk: boolean;
}

export interface ProductResearchProvider {
  id: string;
  name: string;
  channel: string;
  priority: number;
  integrationMode: string;
  pricingHint: string;
  bestFor: string[];
  coreSignals: string[];
  limitations: string[];
  setupActions: string[];
  credentialEnvVars: string[];
  enabled: boolean;
  collectionModes: string[];
  automationLevel: "high" | "medium" | "low";
  dataQuality: "high" | "medium" | "low";
  imageSupport: "product_image" | "creative_image" | "scene_image" | "none";
  freeTier: boolean;
  contributionSummary: string;
  contributionFields: string[];
  collectionNotes: string[];
}

export interface ProductVisual {
  imageUrl: string;
  imageSource: string;
  imageRole: "product" | "marketplace" | "creative" | "scene_fallback";
  licenseNote: string;
  confidence: number;
  sourceUrl?: string;
}

export interface ProductMarketSource {
  providerId: string;
  providerName: string;
  collectionMode: string;
  automationLevel: "high" | "medium" | "low";
  dataQuality: "high" | "medium" | "low";
  imageSupport: "product_image" | "creative_image" | "scene_image" | "none";
  freeTier: boolean;
  status: "ready" | "needs_key" | "manual" | "fallback";
  contributionScore: number;
  fields: string[];
  explanation: string;
  actionLabel: string;
  sourceUrl?: string;
}

export interface ProductCollectionStep {
  key: string;
  label: string;
  mode: "manual_input" | "official_api" | "public_page_capture" | "csv_import" | "fallback_image";
  priority: number;
  providerIds: string[];
  expectedFields: string[];
  qualityImpact: string;
  automationHint: string;
}

export interface ProductOpportunitySignal {
  key: string;
  label: string;
  value: string;
  score: number;
  source: string;
  weight: number;
  explanation: string;
}

export interface ProductValidationCheck {
  key: string;
  label: string;
  status: "passed" | "watch" | "missing";
  detail: string;
  source: string;
}

export interface ProductOpportunityReport {
  productId: string;
  productName: string;
  category: string;
  visual: ProductVisual;
  score: number;
  confidence: number;
  level: "launch_candidate" | "validate_more" | "needs_data";
  recommendedProviders: string[];
  marketSources: ProductMarketSource[];
  collectionPlan: ProductCollectionStep[];
  signals: ProductOpportunitySignal[];
  checks: ProductValidationCheck[];
  nextActions: string[];
  riskFlags: string[];
  sourceTrace: string[];
}

export interface MarketIngestionItem {
  sourceProductId: string;
  productName: string;
  imageUrl?: string;
  sourceUrl?: string;
  status: "created" | "skipped" | "failed";
  reason?: string;
  productId?: string;
}

export interface MarketIngestionRun {
  id: string;
  providerId: string;
  keyword: string;
  status: "completed" | "skipped" | "failed";
  requestedLimit: number;
  createdCount: number;
  skippedCount: number;
  items: MarketIngestionItem[];
  message?: string;
  startedAt: string;
  finishedAt: string;
  nextAllowedAt?: string;
}

// Generated content
export interface GeneratedContent {
  id: string;
  taskId: string;
  text: string;
  score: number;
  riskFlags: string[];
  sourceTrace: string[];
  reviewStatus: "pending" | "approved" | "rejected" | "rewriting";
  editedText?: string;
  qualityReport: QualityReport;
  createdAt: string;
}

export interface QualityReport {
  naturalness: number;
  specificity: number;
  factConsistency: number;
  platformFit: number;
  repetitionRisk: number;
  exaggerationRisk: number;
  overallScore: number;
}

// Generation task
export interface GenerationTask {
  id: string;
  productId: string;
  productName?: string;
  config: GenerationConfig;
  status: "pending" | "generating" | "completed" | "failed";
  contents: GeneratedContent[];
  createdAt: string;
}

// Review record
export interface ReviewRecord {
  id: string;
  contentId: string;
  action: "approved" | "rejected" | "rewrite_requested";
  comment?: string;
  reviewer: string;
  createdAt: string;
}

// Dashboard stats
export interface DashboardStats {
  totalProducts: number;
  totalFeedbacks: number;
  totalGenerations: number;
  pendingReviews: number;
  approvedToday: number;
  averageScore: number;
  riskIntercepted: number;
  weeklyGenerations: number[];
}

// Content type labels
export const contentTypeLabels: Record<ContentType, string> = {
  review_draft: "好评草稿",
  experience_copy: "使用体验",
  recommendation: "推荐语",
  review_invitation: "评价邀请",
  share_guide: "晒单引导",
  cs_followup: "客服回访",
  detail_page: "详情页口碑",
};

export const platformLabels: Record<Platform, string> = {
  taobao: "淘宝",
  tmall: "天猫",
  jd: "京东",
  pdd: "拼多多",
  douyin: "抖音",
  xiaohongshu: "小红书",
  independent: "独立站",
};

export const toneLabels: Record<Tone, string> = {
  natural: "自然",
  sincere: "真诚",
  lively: "活泼",
  professional: "专业",
  brief: "简短",
  detailed: "细节丰富",
};

export const lengthLabels: Record<Length, string> = {
  short: "短句",
  medium: "中等",
  long: "长段",
};

export const personaLabels: Record<Persona, string> = {
  first_person: "第一人称",
  third_person: "第三人称",
  merchant: "商家口吻",
};

export const reviewStatusLabels: Record<string, string> = {
  pending: "待审核",
  approved: "已通过",
  rejected: "已驳回",
  rewriting: "重写中",
};
