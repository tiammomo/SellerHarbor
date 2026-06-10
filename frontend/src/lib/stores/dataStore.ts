import { create } from "zustand";
import { apiClient, type CreateFeedbackPayload, type CreateProductPayload } from "@/lib/api/client";
import type {
  Product,
  Feedback,
  GenerationTask,
  GeneratedContent,
  DashboardStats,
  GenerationConfig,
  ProductOpportunityReport,
  ProductResearchProvider,
  PlatformRule,
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

interface DataState {
  products: Product[];
  feedbacks: Feedback[];
  tasks: GenerationTask[];
  contents: GeneratedContent[];
  dashboardStats: DashboardStats;
  platformRules: PlatformRule[];
  productResearchProviders: ProductResearchProvider[];
  productOpportunityReports: ProductOpportunityReport[];
  loading: boolean;
  initialized: boolean;
  error?: string;
  initialize: () => Promise<void>;
  refreshAll: () => Promise<void>;
  createProduct: (product: CreateProductPayload) => Promise<Product>;
  createFeedback: (feedback: CreateFeedbackPayload) => Promise<Feedback>;
  createGeneration: (config: GenerationConfig) => Promise<GenerationTask>;
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
  platformRules: [],
  productResearchProviders: [],
  productOpportunityReports: [],
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
        platformRules,
        productResearchProviders,
        productOpportunityReports,
      ] = await Promise.all([
        apiClient.getProducts(),
        apiClient.getFeedbacks(),
        apiClient.getTasks(),
        apiClient.getContents(),
        apiClient.getDashboard(),
        apiClient.getPlatformRules(),
        apiClient.getProductResearchProviders(),
        apiClient.getProductOpportunityReports(),
      ]);

      set({
        products,
        feedbacks,
        tasks,
        contents,
        dashboardStats,
        platformRules,
        productResearchProviders,
        productOpportunityReports,
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
