// Product types
export interface Product {
  id: string;
  tenantId: string;
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
  tenantId: string;
  productId: string;
  productName?: string;
  sourceType: "customer_review" | "cs_summary" | "after_sales" | "authorized";
  sourceSummary: string;
  confirmedFacts: string[];
  subjectiveOpinions: string[];
  consentStatus: "confirmed" | "pending" | "not_required";
  createdAt: string;
}

export interface FeedbackOrganization {
  productId: string;
  productName?: string;
  sourceType: Feedback["sourceType"];
  consentStatus: Feedback["consentStatus"];
  sourceSummary: string;
  confirmedFacts: string[];
  subjectiveOpinions: string[];
  uncertainClaims: string[];
  riskFlags: string[];
  recommendedContentTypes: ContentType[];
  readinessScore: number;
  nextActions: string[];
  sourceTrace: string[];
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
  | "independent"
  | "temu"
  | "tiktok_shop";

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
  sourceImageUrl?: string;
  imageStorageKey?: string;
  imageStorageStatus?: "stored" | "source_url" | "failed";
  sourceUrl?: string;
  status: "created" | "skipped" | "failed";
  reason?: string;
  productId?: string;
}

export interface MarketIngestionRun {
  id: string;
  tenantId: string;
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
  tenantId: string;
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
  tenantId: string;
  productId: string;
  productName?: string;
  config: GenerationConfig;
  status: "pending" | "generating" | "completed" | "failed";
  message?: string;
  contents: GeneratedContent[];
  createdAt: string;
  updatedAt?: string;
}

// Review record
export interface ReviewRecord {
  id: string;
  tenantId: string;
  contentId: string;
  action: "approved" | "rejected" | "rewrite_requested";
  comment?: string;
  reviewer: string;
  createdAt: string;
}

export interface AuditEvent {
  id: string;
  tenantId: string;
  actor: string;
  action: string;
  resourceType: string;
  resourceId?: string;
  metadata: Record<string, unknown>;
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

export interface BusinessProductGap {
  productId: string;
  productName: string;
  category: string;
  gap: "missing_feedback" | "weak_product_profile" | "missing_forbidden_claims";
  detail: string;
  nextActionHref: string;
}

export interface BusinessEvidenceCoverage {
  totalProducts: number;
  productsWithUsableFeedback: number;
  productsWithoutUsableFeedback: number;
  readyProducts: number;
  coverageRate: number;
  gaps: BusinessProductGap[];
}

export interface BusinessReviewFunnel {
  pending: number;
  approved: number;
  rejected: number;
  rewriting: number;
  exportable: number;
  approvalRate: number;
}

export interface BusinessContentMixItem {
  contentType: ContentType;
  label: string;
  count: number;
  share: number;
}

export interface BusinessRiskBreakdownItem {
  flag: string;
  label: string;
  count: number;
  level: "info" | "warning" | "critical";
  action: string;
}

export interface BusinessRecommendedAction {
  key: string;
  label: string;
  detail: string;
  priority: number;
  href: string;
  tone: "primary" | "warning" | "success" | "neutral";
}

export interface BusinessOverview {
  positioning: string;
  primaryUseCases: string[];
  evidenceCoverage: BusinessEvidenceCoverage;
  reviewFunnel: BusinessReviewFunnel;
  contentMix: BusinessContentMixItem[];
  riskBreakdown: BusinessRiskBreakdownItem[];
  recommendedActions: BusinessRecommendedAction[];
  generatedAt: string;
}

export type CommercePlatform = "temu" | "tiktok_shop";

export interface CommerceKpi {
  key: string;
  label: string;
  value: number | string;
  unit: string;
  tone: "primary" | "warning" | "success" | "neutral";
  detail: string;
}

export interface CommercePlatformSummary {
  platform: CommercePlatform;
  label: string;
  totalListings: number;
  readyListings: number;
  watchListings: number;
  missingListings: number;
  readinessRate: number;
  priorityAction: string;
}

export interface CommerceWarehouseSummary {
  key: string;
  name: string;
  country: string;
  platforms: CommercePlatform[];
  totalSkus: number;
  totalUnits: number;
  reservedUnits: number;
  lowStockSkus: number;
  stockHealthRate: number;
}

export interface CommerceInventoryAlert {
  productId: string;
  productName: string;
  sku: string;
  warehouseKey: string;
  warehouseName: string;
  availableStock: number;
  reservedStock: number;
  safetyStock: number;
  status: "healthy" | "low_stock" | "out_of_stock";
  detail: string;
  nextActionHref: string;
}

export interface CommerceHotProduct {
  productId: string;
  productName: string;
  category: string;
  sku: string;
  heatScore: number;
  heatLevel: "hot" | "rising" | "steady" | "needs_attention";
  weeklySales: number;
  rating: number;
  reviewCount: number;
  availableStock: number;
  platforms: CommercePlatform[];
  nextAction: string;
}

export interface CommerceOverview {
  positioning: string;
  operatingFocus: string[];
  kpis: CommerceKpi[];
  platforms: CommercePlatformSummary[];
  warehouses: CommerceWarehouseSummary[];
  inventoryAlerts: CommerceInventoryAlert[];
  hotProducts: CommerceHotProduct[];
  recommendedActions: BusinessRecommendedAction[];
  generatedAt: string;
}

export interface StoreCapability {
  key: string;
  label: string;
  mode: "manual" | "read" | "write" | "event";
  status: "ready" | "planned" | "needs_credentials" | "needs_permission" | "blocked";
  detail: string;
  riskLevel: "low" | "medium" | "high";
}

export interface StoreProfile {
  id: string;
  tenantId: string;
  name: string;
  platform: CommercePlatform;
  platformLabel: string;
  status: "active" | "planned" | "needs_credentials" | "disabled";
  region: string;
  externalSellerId?: string;
  isDefault: boolean;
  defaultWarehouse: string;
  sharedInventoryGroup: string;
  credentialScope: string;
  connectionStatus: "ready" | "needs_credentials" | "needs_authorization" | "planned" | "disabled";
  capabilities: StoreCapability[];
  notes: string[];
}

export interface StoreExpansionSlot {
  key: string;
  label: string;
  platform: CommercePlatform;
  status: "planned" | "ready_for_config";
  detail: string;
  requiredEnvVars: string[];
}

export interface StoreDataBoundary {
  key: string;
  label: string;
  currentState: string;
  nextSchema: string;
  reason: string;
}

export interface StoreRegistry {
  tenantId: string;
  mode: "single_store" | "multi_store_ready";
  defaultStoreId: string;
  multiStoreEnabled: boolean;
  stores: StoreProfile[];
  expansionSlots: StoreExpansionSlot[];
  dataBoundaries: StoreDataBoundary[];
  nextActions: string[];
  updatedAt: string;
}

export interface LlmHealth {
  status: "healthy" | "degraded" | "unavailable" | "unconfigured" | "skipped";
  configured: boolean;
  provider: string;
  model: string;
  baseUrl: string;
  detail: string;
  latencyMs?: number | null;
}

export interface ReadinessCheck {
  key: string;
  label: string;
  status: "healthy" | "degraded" | "unavailable" | "unconfigured" | "skipped" | "enabled";
  severity: "critical" | "warning";
  detail: string;
  metadata?: Record<string, unknown>;
}

export interface SystemReadiness {
  status: "healthy" | "degraded" | "unavailable";
  environment: string;
  time: string;
  checks: ReadinessCheck[];
}

export interface TemuRequirement {
  key: string;
  label: string;
  status: "ready" | "missing" | "manual";
  detail: string;
  envVars: string[];
}

export interface TemuCapability {
  key: string;
  label: string;
  mode: "read" | "write" | "event";
  status: "ready" | "planned" | "needs_permission" | "blocked";
  detail: string;
  requiredPermission: string;
  riskLevel: "low" | "medium" | "high";
}

export interface TemuIntegrationStatus {
  platform: "temu";
  label: string;
  configured: boolean;
  readiness: "ready" | "needs_credentials" | "needs_authorization" | "planned";
  mode: "read_only_first" | "disabled";
  region: string;
  sandbox: boolean;
  apiBaseUrl: string;
  credentialEnvVars: string[];
  requirements: TemuRequirement[];
  capabilities: TemuCapability[];
  nextActions: string[];
  docs: string[];
  updatedAt: string;
}

// Content type labels
export const contentTypeLabels: Record<ContentType, string> = {
  review_draft: "口碑草稿",
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
  temu: "Temu",
  tiktok_shop: "TikTok Shop",
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
