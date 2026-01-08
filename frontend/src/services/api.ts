import axios from "axios";
import { useAuthStore } from "@/stores/authStore";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          window.location.href = "/login";
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),

  register: (email: string, password: string, full_name?: string) =>
    api.post("/auth/register", { email, password, full_name }),

  me: () => api.get("/auth/me"),

  logout: () => api.post("/auth/logout"),
};

// Deployments API
export const deploymentsAPI = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }) => {
    const response = await api.get("/deployments", { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/deployments/${id}`);
    return response.data;
  },

  create: async (data: CreateDeploymentData) => {
    const response = await api.post("/deployments", data);
    return response.data;
  },

  update: async (id: string, data: Partial<CreateDeploymentData>) => {
    const response = await api.patch(`/deployments/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/deployments/${id}`);
    return response.data;
  },

  start: async (id: string) => {
    const response = await api.post(`/deployments/${id}/start`);
    return response.data;
  },

  stop: async (id: string) => {
    const response = await api.post(`/deployments/${id}/stop`);
    return response.data;
  },

  redeploy: async (id: string) => {
    const response = await api.post(`/deployments/${id}/redeploy`);
    return response.data;
  },
};

// RAG API
export const ragAPI = {
  listCollections: async () => {
    const response = await api.get("/rag/collections");
    return response.data;
  },

  createCollection: async (data: { name: string; description?: string }) => {
    const response = await api.post("/rag/collections", data);
    return response.data;
  },

  deleteCollection: async (name: string) => {
    const response = await api.delete(`/rag/collections/${name}`);
    return response.data;
  },

  listDocuments: async (collectionName?: string, page?: number) => {
    const response = await api.get("/rag/documents", {
      params: { collection_name: collectionName, page },
    });
    return response.data;
  },

  uploadDocument: async (collectionName: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post(
      `/rag/documents?collection_name=${collectionName}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return response.data;
  },

  deleteDocument: async (id: string) => {
    const response = await api.delete(`/rag/documents/${id}`);
    return response.data;
  },

  query: async (collectionName: string, query: string, topK?: number) => {
    const response = await api.post("/rag/query", {
      collection_name: collectionName,
      query,
      top_k: topK,
    });
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  getDashboard: async () => {
    const response = await api.get("/analytics/dashboard");
    return response.data;
  },

  getUsage: async (period?: string, params?: { deployment_id?: string }) => {
    const response = await api.get("/analytics/usage", {
      params: { period, ...params },
    });
    return response.data;
  },

  getUsageTimeseries: async (
    metric: string,
    period?: string,
    params?: { deployment_id?: string }
  ) => {
    const response = await api.get("/analytics/usage/timeseries", {
      params: { metric, period, ...params },
    });
    return response.data;
  },

  getModels: async (period?: string) => {
    const response = await api.get("/analytics/models", { params: { period } });
    return response.data;
  },

  getCosts: async (period?: string) => {
    const response = await api.get("/analytics/costs", { params: { period } });
    return response.data;
  },

  getErrors: async (period?: string) => {
    const response = await api.get("/analytics/errors", { params: { period } });
    return response.data;
  },
};

export const apiKeysAPI = {
  list: async () => {
    const response = await api.get("/api-keys");
    return response.data;
  },

  create: async (data: {
    name: string;
    scopes?: string[];
    expires_days?: number;
  }) => {
    const response = await api.post("/api-keys", data);
    return response.data;
  },

  delete: async (keyId: string) => {
    const response = await api.delete(`/api-keys/${keyId}`);
    return response.data;
  },
};

export const playgroundAPI = {
  chat: async (data: {
    messages: Array<{ role: string; content: string }>;
    model: string;
    provider: string;
    temperature: number;
    max_tokens: number;
    system_prompt?: string;
    stream: boolean;
  }) => {
    const response = await api.post("/playground/chat", data);
    return response.data;
  },

  getModels: async () => {
    const response = await api.get("/playground/models");
    return response.data;
  },

  getPresets: async () => {
    const response = await api.get("/playground/presets");
    return response.data;
  },
};

// Types
export interface CreateDeploymentData {
  name: string;
  description?: string;
  deployment_type: "rag" | "agent" | "chat" | "completion" | "custom";
  config: {
    model: {
      provider: string;
      model: string;
      temperature: number;
      max_tokens: number;
    };
    rag?: {
      collection_name: string;
      top_k: number;
      score_threshold: number;
    };
  };
  replicas?: number;
}

export interface RAGQueryData {
  query: string;
  collection_name: string;
  top_k?: number;
  score_threshold?: number;
  model?: string;
  temperature?: number;
}
