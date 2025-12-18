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
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get("/deployments", { params }),

  get: (id: string) => api.get(`/deployments/${id}`),

  create: (data: CreateDeploymentData) => api.post("/deployments", data),

  update: (id: string, data: Partial<CreateDeploymentData>) =>
    api.patch(`/deployments/${id}`, data),

  delete: (id: string) => api.delete(`/deployments/${id}`),

  start: (id: string) => api.post(`/deployments/${id}/start`),

  stop: (id: string) => api.post(`/deployments/${id}/stop`),

  redeploy: (id: string) => api.post(`/deployments/${id}/redeploy`),
};

// RAG API
export const ragAPI = {
  collections: {
    list: () => api.get("/rag/collections"),
    create: (data: { name: string; description?: string }) =>
      api.post("/rag/collections", data),
    delete: (name: string) => api.delete(`/rag/collections/${name}`),
  },

  documents: {
    list: (params?: { collection_name?: string; page?: number }) =>
      api.get("/rag/documents", { params }),
    upload: (file: File, collection_name: string) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.post(
        `/rag/documents?collection_name=${collection_name}`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
    },
    delete: (id: string) => api.delete(`/rag/documents/${id}`),
  },

  query: (data: RAGQueryData) => api.post("/rag/query", data),

  search: (query: string, collection_name: string, top_k?: number) =>
    api.post("/rag/search", { query, collection_name, top_k }),
};

// Analytics API
export const analyticsAPI = {
  dashboard: () => api.get("/analytics/dashboard"),

  usage: (params?: { period?: string; deployment_id?: string }) =>
    api.get("/analytics/usage", { params }),

  timeseries: (metric: string, period?: string) =>
    api.get("/analytics/usage/timeseries", { params: { metric, period } }),

  models: (period?: string) =>
    api.get("/analytics/models", { params: { period } }),

  costs: (period?: string) =>
    api.get("/analytics/costs", { params: { period } }),

  errors: (period?: string) =>
    api.get("/analytics/errors", { params: { period } }),
};

export const apiKeysAPI = {
  list: () => api.get("/api-keys"),
  create: (data: { name: string; scopes: string[]; expires_days?: number }) =>
    api.post("/api-keys", data),
  revoke: (keyId: string) => api.delete(`/api-keys/${keyId}`),
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
    const response = await api.post('/playground/chat', data);
    return response.data;
  },
  
  getModels: async () => {
    const response = await api.get('/playground/models');
    return response.data;
  },
  
  getPresets: async () => {
    const response = await api.get('/playground/presets');
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
