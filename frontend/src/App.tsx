import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { Toaster } from "@/components/ui/toaster";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { DeploymentsPage } from "@/pages/DeploymentsPage";
import { DeploymentDetailPage } from "@/pages/DeploymentDetailPage";
import { RAGPage } from "@/pages/RAGPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { PlaygroundPage } from "./pages/PlaygroundPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="deployments" element={<DeploymentsPage />} />
          <Route path="deployments/:id" element={<DeploymentDetailPage />} />
          <Route path="playground" element={<PlaygroundPage />} />
          <Route path="rag" element={<RAGPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}

export default App;
