from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    id: str
    tenantId: str = "local"
    name: str
    category: str
    attributes: dict[str, str] = Field(default_factory=dict)
    sellingPoints: list[str] = Field(default_factory=list)
    targetAudiences: list[str] = Field(default_factory=list)
    usageScenarios: list[str] = Field(default_factory=list)
    forbiddenClaims: list[str] = Field(default_factory=list)
    brandVoiceId: str | None = None
    createdAt: str
    updatedAt: str


class CreateProduct(BaseModel):
    name: str
    category: str
    attributes: dict[str, str] = Field(default_factory=dict)
    sellingPoints: list[str] = Field(default_factory=list)
    targetAudiences: list[str] = Field(default_factory=list)
    usageScenarios: list[str] = Field(default_factory=list)
    forbiddenClaims: list[str] = Field(default_factory=list)
    brandVoiceId: str | None = None


SourceType = Literal["customer_review", "cs_summary", "after_sales", "authorized"]
ConsentStatus = Literal["confirmed", "pending", "not_required"]


class Feedback(BaseModel):
    id: str
    tenantId: str = "local"
    productId: str
    productName: str | None = None
    sourceType: SourceType
    sourceSummary: str
    confirmedFacts: list[str] = Field(default_factory=list)
    subjectiveOpinions: list[str] = Field(default_factory=list)
    consentStatus: ConsentStatus
    createdAt: str


class CreateFeedback(BaseModel):
    productId: str
    sourceType: SourceType
    sourceSummary: str
    confirmedFacts: list[str] = Field(default_factory=list)
    subjectiveOpinions: list[str] = Field(default_factory=list)
    consentStatus: ConsentStatus = "confirmed"


ContentType = Literal[
    "review_draft",
    "experience_copy",
    "recommendation",
    "review_invitation",
    "share_guide",
    "cs_followup",
    "detail_page",
]
Platform = Literal["taobao", "tmall", "jd", "pdd", "douyin", "xiaohongshu", "independent", "temu", "tiktok_shop"]
Tone = Literal["natural", "sincere", "lively", "professional", "brief", "detailed"]
Length = Literal["short", "medium", "long"]
Persona = Literal["first_person", "third_person", "merchant"]
ReviewStatus = Literal["pending", "approved", "rejected", "rewriting"]


class GenerationConfig(BaseModel):
    productId: str
    feedbackId: str | None = None
    contentType: ContentType = "review_draft"
    platform: Platform = "taobao"
    merchantType: str | None = None
    tone: Tone = "natural"
    length: Length = "medium"
    persona: Persona = "first_person"
    scenario: str | None = None
    count: int = Field(default=1, ge=1, le=20)


class OrganizeFeedbackRequest(BaseModel):
    productId: str
    rawText: str = Field(min_length=4)
    sourceType: SourceType = "customer_review"
    consentStatus: ConsentStatus = "confirmed"
    platform: Platform | None = None


class FeedbackOrganization(BaseModel):
    productId: str
    productName: str | None = None
    sourceType: SourceType
    consentStatus: ConsentStatus
    sourceSummary: str
    confirmedFacts: list[str] = Field(default_factory=list)
    subjectiveOpinions: list[str] = Field(default_factory=list)
    uncertainClaims: list[str] = Field(default_factory=list)
    riskFlags: list[str] = Field(default_factory=list)
    recommendedContentTypes: list[ContentType] = Field(default_factory=list)
    readinessScore: int = 0
    nextActions: list[str] = Field(default_factory=list)
    sourceTrace: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    naturalness: int = 80
    specificity: int = 80
    factConsistency: int = 80
    platformFit: int = 80
    repetitionRisk: int = 8
    exaggerationRisk: int = 8
    overallScore: int = 80


class GeneratedContent(BaseModel):
    id: str
    tenantId: str = "local"
    taskId: str
    text: str
    score: int
    riskFlags: list[str] = Field(default_factory=list)
    sourceTrace: list[str] = Field(default_factory=list)
    reviewStatus: ReviewStatus = "pending"
    editedText: str | None = None
    qualityReport: QualityReport
    createdAt: str


class GenerationTask(BaseModel):
    id: str
    tenantId: str = "local"
    productId: str
    productName: str | None = None
    config: GenerationConfig
    status: Literal["pending", "generating", "completed", "failed"] = "completed"
    message: str | None = None
    contents: list[GeneratedContent] = Field(default_factory=list)
    createdAt: str
    updatedAt: str | None = None


class ReviewRequest(BaseModel):
    action: str | None = None
    status: ReviewStatus | None = None
    comment: str | None = None
    reviewer: str = "local-user"
    editedText: str | None = None


class ReviewRecord(BaseModel):
    id: str
    tenantId: str = "local"
    contentId: str
    action: str
    comment: str | None = None
    reviewer: str
    createdAt: str


class AuditEvent(BaseModel):
    id: str
    tenantId: str = "local"
    actor: str
    action: str
    resourceType: str
    resourceId: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    createdAt: str


class DashboardStats(BaseModel):
    totalProducts: int = 0
    totalFeedbacks: int = 0
    totalGenerations: int = 0
    pendingReviews: int = 0
    approvedToday: int = 0
    averageScore: float = 0
    riskIntercepted: int = 0
    weeklyGenerations: list[int] = Field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0])


class BusinessProductGap(BaseModel):
    productId: str
    productName: str
    category: str
    gap: Literal["missing_feedback", "weak_product_profile", "missing_forbidden_claims"]
    detail: str
    nextActionHref: str


class BusinessEvidenceCoverage(BaseModel):
    totalProducts: int = 0
    productsWithUsableFeedback: int = 0
    productsWithoutUsableFeedback: int = 0
    readyProducts: int = 0
    coverageRate: int = 0
    gaps: list[BusinessProductGap] = Field(default_factory=list)


class BusinessReviewFunnel(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    rewriting: int = 0
    exportable: int = 0
    approvalRate: int = 0


class BusinessContentMixItem(BaseModel):
    contentType: ContentType
    label: str
    count: int
    share: int


class BusinessRiskBreakdownItem(BaseModel):
    flag: str
    label: str
    count: int
    level: Literal["info", "warning", "critical"] = "warning"
    action: str


class BusinessRecommendedAction(BaseModel):
    key: str
    label: str
    detail: str
    priority: int = 50
    href: str
    tone: Literal["primary", "warning", "success", "neutral"] = "neutral"


class BusinessOverview(BaseModel):
    positioning: str
    primaryUseCases: list[str]
    evidenceCoverage: BusinessEvidenceCoverage
    reviewFunnel: BusinessReviewFunnel
    contentMix: list[BusinessContentMixItem] = Field(default_factory=list)
    riskBreakdown: list[BusinessRiskBreakdownItem] = Field(default_factory=list)
    recommendedActions: list[BusinessRecommendedAction] = Field(default_factory=list)
    generatedAt: str


CommercePlatform = Literal["temu", "tiktok_shop"]
CommerceTone = Literal["primary", "warning", "success", "neutral"]


class CommerceKpi(BaseModel):
    key: str
    label: str
    value: int | float | str
    unit: str = ""
    tone: CommerceTone = "neutral"
    detail: str = ""


class CommercePlatformSummary(BaseModel):
    platform: CommercePlatform
    label: str
    totalListings: int = 0
    readyListings: int = 0
    watchListings: int = 0
    missingListings: int = 0
    readinessRate: int = 0
    priorityAction: str


class CommerceWarehouseSummary(BaseModel):
    key: str
    name: str
    country: str
    platforms: list[CommercePlatform] = Field(default_factory=list)
    totalSkus: int = 0
    totalUnits: int = 0
    reservedUnits: int = 0
    lowStockSkus: int = 0
    stockHealthRate: int = 0


class CommerceInventoryAlert(BaseModel):
    productId: str
    productName: str
    sku: str
    warehouseKey: str
    warehouseName: str
    availableStock: int = 0
    reservedStock: int = 0
    safetyStock: int = 0
    status: Literal["healthy", "low_stock", "out_of_stock"] = "healthy"
    detail: str
    nextActionHref: str


class CommerceHotProduct(BaseModel):
    productId: str
    productName: str
    category: str
    sku: str
    heatScore: int = 0
    heatLevel: Literal["hot", "rising", "steady", "needs_attention"] = "steady"
    weeklySales: int = 0
    rating: float = 0
    reviewCount: int = 0
    availableStock: int = 0
    platforms: list[CommercePlatform] = Field(default_factory=list)
    nextAction: str


class CommerceOverview(BaseModel):
    positioning: str
    operatingFocus: list[str]
    kpis: list[CommerceKpi] = Field(default_factory=list)
    platforms: list[CommercePlatformSummary] = Field(default_factory=list)
    warehouses: list[CommerceWarehouseSummary] = Field(default_factory=list)
    inventoryAlerts: list[CommerceInventoryAlert] = Field(default_factory=list)
    hotProducts: list[CommerceHotProduct] = Field(default_factory=list)
    recommendedActions: list[BusinessRecommendedAction] = Field(default_factory=list)
    generatedAt: str


StoreStatus = Literal["active", "planned", "needs_credentials", "disabled"]
StoreConnectionStatus = Literal["ready", "needs_credentials", "needs_authorization", "planned", "disabled"]
StoreCapabilityMode = Literal["manual", "read", "write", "event"]
StoreCapabilityStatus = Literal["ready", "planned", "needs_credentials", "needs_permission", "blocked"]


class StoreCapability(BaseModel):
    key: str
    label: str
    mode: StoreCapabilityMode
    status: StoreCapabilityStatus
    detail: str
    riskLevel: Literal["low", "medium", "high"] = "medium"


class StoreProfile(BaseModel):
    id: str
    tenantId: str = "local"
    name: str
    platform: CommercePlatform
    platformLabel: str
    status: StoreStatus
    region: str
    externalSellerId: str | None = None
    isDefault: bool = False
    defaultWarehouse: str
    sharedInventoryGroup: str
    credentialScope: str
    connectionStatus: StoreConnectionStatus
    capabilities: list[StoreCapability] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class StoreExpansionSlot(BaseModel):
    key: str
    label: str
    platform: CommercePlatform
    status: Literal["planned", "ready_for_config"]
    detail: str
    requiredEnvVars: list[str] = Field(default_factory=list)


class StoreDataBoundary(BaseModel):
    key: str
    label: str
    currentState: str
    nextSchema: str
    reason: str


class StoreRegistry(BaseModel):
    tenantId: str = "local"
    mode: Literal["single_store", "multi_store_ready"] = "single_store"
    defaultStoreId: str
    multiStoreEnabled: bool = False
    stores: list[StoreProfile] = Field(default_factory=list)
    expansionSlots: list[StoreExpansionSlot] = Field(default_factory=list)
    dataBoundaries: list[StoreDataBoundary] = Field(default_factory=list)
    nextActions: list[str] = Field(default_factory=list)
    updatedAt: str


class TemuRequirement(BaseModel):
    key: str
    label: str
    status: Literal["ready", "missing", "manual"]
    detail: str
    envVars: list[str] = Field(default_factory=list)


class TemuCapability(BaseModel):
    key: str
    label: str
    mode: Literal["read", "write", "event"]
    status: Literal["ready", "planned", "needs_permission", "blocked"]
    detail: str
    requiredPermission: str
    riskLevel: Literal["low", "medium", "high"] = "medium"


class TemuIntegrationStatus(BaseModel):
    platform: Literal["temu"] = "temu"
    label: str = "Temu"
    configured: bool = False
    readiness: Literal["ready", "needs_credentials", "needs_authorization", "planned"] = "needs_credentials"
    mode: Literal["read_only_first", "disabled"] = "read_only_first"
    region: str
    sandbox: bool = False
    apiBaseUrl: str
    credentialEnvVars: list[str] = Field(default_factory=list)
    requirements: list[TemuRequirement] = Field(default_factory=list)
    capabilities: list[TemuCapability] = Field(default_factory=list)
    nextActions: list[str] = Field(default_factory=list)
    docs: list[str] = Field(default_factory=list)
    updatedAt: str


class ProductResearchProvider(BaseModel):
    id: str
    name: str
    channel: str
    priority: int
    integrationMode: str
    pricingHint: str
    bestFor: list[str]
    coreSignals: list[str]
    limitations: list[str]
    setupActions: list[str]
    credentialEnvVars: list[str] = Field(default_factory=list)
    enabled: bool = False
    collectionModes: list[str] = Field(default_factory=list)
    automationLevel: Literal["high", "medium", "low"] = "medium"
    dataQuality: Literal["high", "medium", "low"] = "medium"
    imageSupport: Literal["product_image", "creative_image", "scene_image", "none"] = "none"
    freeTier: bool = False
    contributionSummary: str = ""
    contributionFields: list[str] = Field(default_factory=list)
    collectionNotes: list[str] = Field(default_factory=list)


class ProductVisual(BaseModel):
    imageUrl: str
    imageSource: str
    imageRole: Literal["product", "marketplace", "creative", "scene_fallback"]
    licenseNote: str
    confidence: int = 50
    sourceUrl: str | None = None


class ProductMarketSource(BaseModel):
    providerId: str
    providerName: str
    collectionMode: str
    automationLevel: Literal["high", "medium", "low"]
    dataQuality: Literal["high", "medium", "low"]
    imageSupport: Literal["product_image", "creative_image", "scene_image", "none"]
    freeTier: bool = False
    status: Literal["ready", "needs_key", "manual", "fallback"]
    contributionScore: int
    fields: list[str]
    explanation: str
    actionLabel: str
    sourceUrl: str | None = None


class ProductCollectionStep(BaseModel):
    key: str
    label: str
    mode: Literal["manual_input", "official_api", "public_page_capture", "csv_import", "fallback_image"]
    priority: int
    providerIds: list[str]
    expectedFields: list[str]
    qualityImpact: str
    automationHint: str


class ProductOpportunitySignal(BaseModel):
    key: str
    label: str
    value: str
    score: int
    source: str
    weight: float
    explanation: str


class ProductValidationCheck(BaseModel):
    key: str
    label: str
    status: Literal["passed", "watch", "missing"]
    detail: str
    source: str


class ProductOpportunityReport(BaseModel):
    productId: str
    productName: str
    category: str
    visual: ProductVisual
    score: int
    confidence: int
    level: Literal["launch_candidate", "validate_more", "needs_data"]
    recommendedProviders: list[str]
    marketSources: list[ProductMarketSource] = Field(default_factory=list)
    collectionPlan: list[ProductCollectionStep] = Field(default_factory=list)
    signals: list[ProductOpportunitySignal]
    checks: list[ProductValidationCheck]
    nextActions: list[str]
    riskFlags: list[str] = Field(default_factory=list)
    sourceTrace: list[str] = Field(default_factory=list)


class MarketIngestionRequest(BaseModel):
    keyword: str = "coffee"
    limit: int = Field(default=3, ge=1, le=8)
    force: bool = False


class MarketIngestionItem(BaseModel):
    sourceProductId: str
    productName: str
    imageUrl: str | None = None
    sourceImageUrl: str | None = None
    imageStorageKey: str | None = None
    imageStorageStatus: Literal["stored", "source_url", "failed"] | None = None
    sourceUrl: str | None = None
    status: Literal["created", "skipped", "failed"]
    reason: str | None = None
    productId: str | None = None


class MarketIngestionRun(BaseModel):
    id: str
    tenantId: str = "local"
    providerId: str
    keyword: str
    status: Literal["completed", "skipped", "failed"]
    requestedLimit: int
    createdCount: int
    skippedCount: int
    items: list[MarketIngestionItem] = Field(default_factory=list)
    message: str | None = None
    startedAt: str
    finishedAt: str
    nextAllowedAt: str | None = None


class PlatformRule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    platform: str
    merchantType: str
    displayName: str
    objective: str
    voice: str
    structure: list[str]
    positiveSignals: list[str]
    avoidClaims: list[str]
    riskTerms: list[str]
    maxShortRunes: int = 100
    requireExperienceEvidence: bool = False
    merchantVoiceReviewRisk: bool = False
