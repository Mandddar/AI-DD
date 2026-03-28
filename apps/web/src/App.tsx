import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { authApi } from "./api/auth";
import { useAuthStore } from "./store/auth";
import { AppShell } from "./components/layout/AppShell";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { DisclaimerPage } from "./pages/auth/DisclaimerPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectsPage } from "./pages/projects/ProjectsPage";
import { DocumentsPage } from "./pages/documents/DocumentsPage";
import { AgentsPage } from "./pages/agents/AgentsPage";
import { AgentRunPage } from "./pages/agents/AgentRunPage";
import { LandingPage } from "./pages/LandingPage";

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuthStore();
  if (isLoading)
    return (
      <div className="flex h-screen items-center justify-center bg-canvas">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-canvas-border border-t-gold" />
          <p className="text-xs text-text-muted">Loading…</p>
        </div>
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  if (!user.disclaimer_accepted) return <Navigate to="/disclaimer" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { setUser, setLoading } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/disclaimer" element={<DisclaimerPage />} />

      {/* Protected */}
      <Route
        element={
          <AuthGuard>
            <AppShell />
          </AuthGuard>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId/documents" element={<DocumentsPage />} />
        <Route path="/projects/:projectId/analysis" element={<AgentsPage />} />
        <Route path="/projects/:projectId/analysis/:runId" element={<AgentRunPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
