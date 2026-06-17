import { create } from "zustand";
import {
  apiClient,
  type CreateFeedbackPayload,
  type CreateProductPayload,
  type IngestOpenFoodFactsPayload,
  type OrganizeFeedbackPayload,
} from "@/lib/api/client";
import type {
  Product,
  Feedback,
  FeedbackOrganization,
  GenerationTask,
  GeneratedContent,
  DashboardStats,
  GenerationConfig,
  MarketIngestionRun,
  ProductOpportunityReport,
  ProductResearchProvider,
  PlatformRule,
  BusinessOverview,
  CommerceOverview,
} from "@/lib/types";

const emptyDashboardStats: DashboardStats = {
  totalProducts: 0,
  totalFeedbacks: 0,
  totalGenerations: 0,
  pendingReviews: 0,
  approvedToday: 0,
  averageScore: 0,
  riskIntercepted: 0,
  weeklyGenerations: [0, 0, 0, 0, 0, 0, 0],
};

const emptyBusinessOverview: BusinessOverview = {
  positioning: "内容与评价运营助手",
  primaryUseCases: ["评价邀请", "客服回访", "商品推荐语", "详情页口碑描述"],
  evidenceCoverage: {
    totalProducts: 0,
    productsWithUsableFeedback: 0,
    productsWithoutUsableFeedback: 0,
    readyProducts: 0,
    coverageRate: 0,
    gaps: [],
  },
  reviewFunnel: {
    pending: 0,
    approved: 0,
    rejected: 0,
    rewriting: 0,
    exportable: 0,
    approvalRate: 0,
  },
  contentMix: [],
  riskBreakdown: [],
  recommendedActions: [],
  generatedAt: "",
};

const emptyCommerceOverview: CommerceOverview = {
  positioning: "SellerHarbor 跨境卖家商品运营港",
  operatingFocus: ["商品主数据收口", "Temu / TikTok Shop 上架管理", "海外仓库存分配", "好评与热款追踪"],
  kpis: [],
  platforms: [],
  warehouses: [],
  inventoryAlerts: [],
  hotProducts: [],
  recommendedActions: [],
  generatedAt: "",
};

interface DataState {
  products: Product[];
  feedbacks: Feedback[];
  tasks: GenerationTask[];
  contents: GeneratedContent[];
  dashboardStats: DashboardStats;
  businessOverview: BusinessOverview;
  commerceOverview: CommerceOverview;
  platformRules: PlatformRule[];
  productResearchProviders: ProductResearchProvider[];
  productOpportunityReports: ProductOpportunityReport[];
  marketIngestionRuns: MarketIngestionRun[];
  loading: boolean;
  initialized: boolean;
  error?: string;
  initialize: () => Promise<void>;
  refreshAll: () => Promise<void>;
  createProduct: (product: CreateProductPayload) => Promise<Product>;
  organizeFeedback: (feedback: OrganizeFeedbackPayload) => Promise<FeedbackOrganization>;
  createFeedback: (feedback: CreateFeedbackPayload) => Promise<Feedback>;
  createGeneration: (config: GenerationConfig) => Promise<GenerationTask>;
  createGenerationJob: (config: GenerationConfig) => Promise<GenerationTask>;
  getGenerationTask: (taskId: string) => Promise<GenerationTask>;
  ingestOpenFoodFacts: (payload: IngestOpenFoodFactsPayload) => Promise<MarketIngestionRun>;
  updateContentReview: (contentId: string, status: GeneratedContent["reviewStatus"]) => Promise<GeneratedContent>;
  getProducts: () => Product[];
  getFeedbacksByProduct: (productId: string) => Feedback[];
  getContentsByTask: (taskId: string) => GeneratedContent[];
  getPendingContents: () => GeneratedContent[];
}

export const useDataStore = create<DataState>((set, get) => ({
  products: [],
  feedbacks: [],
  tasks: [],
  contents: [],
  dashboardStats: emptyDashboardStats,
  businessOverview: emptyBusinessOverview,
  commerceOverview: emptyCommerceOverview,
  platformRules: [],
  productResearchProviders: [],
  productOpportunityReports: [],
  marketIngestionRuns: [],
  loading: false,
  initialized: false,

  initialize: async () => {
    if (get().initialized || get().loading) return;
    await get().refreshAll();
  },

  refreshAll: async () => {
    set({ loading: true, error: undefined });
    try {
      const [
        products,
        feedbacks,
        tasks,
        contents,
        dashboardStats,
        businessOverview,
        commerceOverview,
        platformRules,
      ] = await Promise.all([
        apiClient.getProducts(),
        apiClient.getFeedbacks(),
        apiClient.getTasks(),
        apiClient.getContents(),
        apiClient.getDashboard(),
        apiClient.getBusinessOverview(),
        apiClient.getCommerceOverview(),
        apiClient.getPlatformRules(),
      ]);

      set({
        products,
        feedbacks,
        tasks,
        contents,
        dashboardStats,
        businessOverview,
        commerceOverview,
        platformRules,
        loading: false,
        initialized: true,
      });
    } catch (error) {
      set({
        loading: false,
        initialized: true,
        error: error instanceof Error ? error.message : "加载后端数据失败",
      });
    }
  },

  createProduct: async (payload) => {
    const product = await apiClient.createProduct(payload);
    set((state) => ({
      products: [product, ...state.products],
      dashboardStats: {
        ...state.dashboardStats,
        totalProducts: state.dashboardStats.totalProducts + 1,
      },
    }));
    void get().refreshAll();
    return product;
  },

  organizeFeedback: async (payload) => apiClient.organizeFeedback(payload),

  createFeedback: async (payload) => {
    const feedback = await apiClient.createFeedback(payload);
    set((state) => ({
      feedbacks: [feedback, ...state.feedbacks],
      dashboardStats: {
        ...state.dashboardStats,
        totalFeedbacks: state.dashboardStats.totalFeedbacks + 1,
      },
    }));
    void get().refreshAll();
    return feedback;
  },

  createGeneration: async (config) => {
    const task = await apiClient.createGeneration(config);
    const newContents = task.contents || [];
    set((state) => ({
      tasks: [task, ...state.tasks],
      contents: [...newContents, ...state.contents],
      dashboardStats: {
        ...state.dashboardStats,
        totalGenerations: state.dashboardStats.totalGenerations + newContents.length,
        pendingReviews:
          state.dashboardStats.pendingReviews +
          newContents.filter((content) => content.reviewStatus === "pending").length,
      },
    }));
    void get().refreshAll();
    return task;
  },

  createGenerationJob: async (config) => {
    const task = await apiClient.createGenerationJob(config);
    set((state) => ({
      tasks: [task, ...state.tasks.filter((item) => item.id !== task.id)],
    }));
    return task;
  },

  getGenerationTask: async (taskId) => {
    const task = await apiClient.getGenerationTask(taskId);
    const newContents = task.contents || [];
    set((state) => ({
      tasks: [task, ...state.tasks.filter((item) => item.id !== task.id)],
      contents:
        task.status === "completed"
          ? [...newContents, ...state.contents.filter((content) => content.taskId !== task.id)]
          : state.contents,
      dashboardStats:
        task.status === "completed"
          ? {
              ...state.dashboardStats,
              totalGenerations: Math.max(state.dashboardStats.totalGenerations, state.contents.length + newContents.length),
              pendingReviews: Math.max(
                state.dashboardStats.pendingReviews,
                newContents.filter((content) => content.reviewStatus === "pending").length
              ),
            }
          : state.dashboardStats,
    }));
    if (task.status === "completed") void get().refreshAll();
    return task;
  },

  ingestOpenFoodFacts: async (payload) => {
    const run = await apiClient.ingestOpenFoodFacts(payload);
    set((state) => ({
      marketIngestionRuns: [run, ...state.marketIngestionRuns.filter((item) => item.id !== run.id)],
    }));
    await get().refreshAll();
    return run;
  },

  updateContentReview: async (contentId, status) => {
    const updated = await apiClient.reviewContent(contentId, status);
    const previous = get().contents.find((content) => content.id === contentId);
    const pendingDelta =
      (updated.reviewStatus === "pending" ? 1 : 0) - (previous?.reviewStatus === "pending" ? 1 : 0);
    const approvedTodayDelta =
      (updated.reviewStatus === "approved" ? 1 : 0) - (previous?.reviewStatus === "approved" ? 1 : 0);

    set((state) => ({
      contents: state.contents.map((content) => (content.id === contentId ? updated : content)),
      tasks: state.tasks.map((task) => ({
        ...task,
        contents: task.contents.map((content) => (content.id === contentId ? updated : content)),
      })),
      dashboardStats: {
        ...state.dashboardStats,
        pendingReviews: Math.max(0, state.dashboardStats.pendingReviews + pendingDelta),
        approvedToday: Math.max(0, state.dashboardStats.approvedToday + approvedTodayDelta),
      },
    }));
    void get().refreshAll();
    return updated;
  },

  getProducts: () => get().products,
  getFeedbacksByProduct: (productId) => get().feedbacks.filter((feedback) => feedback.productId === productId),
  getContentsByTask: (taskId) => get().contents.filter((content) => content.taskId === taskId),
  getPendingContents: () => get().contents.filter((content) => content.reviewStatus === "pending"),
}));
