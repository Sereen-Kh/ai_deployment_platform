import { create } from "zustand";

interface Deployment {
  id: string;
  name: string;
  description: string | null;
  deployment_type: string;
  status: string;
  endpoint_url: string | null;
  created_at: string;
}

interface DeploymentState {
  deployments: Deployment[];
  selectedDeployment: Deployment | null;
  isLoading: boolean;
  setDeployments: (deployments: Deployment[]) => void;
  selectDeployment: (deployment: Deployment | null) => void;
  addDeployment: (deployment: Deployment) => void;
  updateDeployment: (id: string, updates: Partial<Deployment>) => void;
  removeDeployment: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useDeploymentStore = create<DeploymentState>((set) => ({
  deployments: [],
  selectedDeployment: null,
  isLoading: false,

  setDeployments: (deployments) => set({ deployments }),

  selectDeployment: (deployment) => set({ selectedDeployment: deployment }),

  addDeployment: (deployment) =>
    set((state) => ({
      deployments: [deployment, ...state.deployments],
    })),

  updateDeployment: (id, updates) =>
    set((state) => ({
      deployments: state.deployments.map((d) =>
        d.id === id ? { ...d, ...updates } : d
      ),
    })),

  removeDeployment: (id) =>
    set((state) => ({
      deployments: state.deployments.filter((d) => d.id !== id),
    })),

  setLoading: (isLoading) => set({ isLoading }),
}));
