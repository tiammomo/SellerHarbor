import type {
  DashboardStats,
  Feedback,
  GeneratedContent,
  GenerationConfig,
  GenerationTask,
  MarketIngestionRun,
  ProductOpportunityReport,
  ProductResearchProvider,
  PlatformRule,
  Product,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:38081/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new ApiError(data?.detail || data?.error || `请求失败: ${response.status}`, response.status);
  }
  return data as T;
}

export type CreateProductPayload = {
  name: string;
  category: string;
  attributes?: Record<string, string>;
  sellingPoints?: string[];
  targetAudiences?: string[];
  usageScenarios?: string[];
  forbiddenClaims?: string[];
  brandVoiceId?: string;
};

export type CreateFeedbackPayload = {
  productId: string;
  sourceType: Feedback["sourceType"];
  sourceSummary: string;
  confirmedFacts?: string[];
  subjectiveOpinions?: string[];
  consentStatus?: Feedback["consentStatus"];
};

export type IngestOpenFoodFactsPayload = {
  keyword?: string;
  limit?: number;
  force?: boolean;
};

export const apiClient = {
  getDashboard: () => request<DashboardStats>("/dashboard"),
  getPlatformRules: () => request<PlatformRule[]>("/rules/platforms"),
  getProductResearchProviders: () => request<ProductResearchProvider[]>("/product-sourcing/providers"),
  getProductOpportunityReports: () => request<ProductOpportunityReport[]>("/product-sourcing/reports"),
  getMarketIngestionRuns: () => request<MarketIngestionRun[]>("/product-sourcing/ingestion-runs"),
  ingestOpenFoodFacts: (payload: IngestOpenFoodFactsPayload) =>
    request<MarketIngestionRun>("/product-sourcing/ingest/open-food-facts", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getProducts: () => request<Product[]>("/products"),
  createProduct: (payload: CreateProductPayload) =>
    request<Product>("/products", { method: "POST", body: JSON.stringify(payload) }),
  getFeedbacks: () => request<Feedback[]>("/feedback"),
  createFeedback: (payload: CreateFeedbackPayload) =>
    request<Feedback>("/feedback", { method: "POST", body: JSON.stringify(payload) }),
  getTasks: () => request<GenerationTask[]>("/generations"),
  getContents: () => request<GeneratedContent[]>("/contents"),
  createGeneration: (payload: GenerationConfig) =>
    request<GenerationTask>("/generations", { method: "POST", body: JSON.stringify(payload) }),
  reviewContent: (contentId: string, status: GeneratedContent["reviewStatus"]) =>
    request<GeneratedContent>(`/contents/${contentId}/review`, {
      method: "POST",
      body: JSON.stringify({
        status,
        action: status === "rewriting" ? "rewrite_requested" : status,
        reviewer: "frontend",
      }),
    }),
};
