from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    id: str
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
Platform = Literal["taobao", "tmall", "jd", "pdd", "douyin", "xiaohongshu", "independent"]
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
    productId: str
    productName: str | None = None
    config: GenerationConfig
    status: Literal["pending", "generating", "completed", "failed"] = "completed"
    contents: list[GeneratedContent] = Field(default_factory=list)
    createdAt: str


class ReviewRequest(BaseModel):
    action: str | None = None
    status: ReviewStatus | None = None
    comment: str | None = None
    reviewer: str = "local-user"
    editedText: str | None = None


class ReviewRecord(BaseModel):
    id: str
    contentId: str
    action: str
    comment: str | None = None
    reviewer: str
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
    sourceUrl: str | None = None
    status: Literal["created", "skipped", "failed"]
    reason: str | None = None
    productId: str | None = None


class MarketIngestionRun(BaseModel):
    id: str
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
