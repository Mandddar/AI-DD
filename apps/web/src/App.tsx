import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { authApi } from "./api/auth";
import { api } from "./api/client";
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
import PlanningPage from "./pages/planning/PlanningPage";
import FinancePage from "./pages/finance/FinancePage";
import ReportsPage from "./pages/reports/ReportsPage";
import AuditLogsPage from "./pages/audit/AuditLogsPage";
import SettingsPage from "./pages/settings/SettingsPage";
import RedFlagsPage from "./pages/redflags/RedFlagsPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import ProjectSettingsPage from "./pages/projects/ProjectSettingsPage";

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

function RoleGuard({ allowedRoles, children }: { allowedRoles: string[]; children: React.ReactNode }) {
  const { user } = useAuthStore();
  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}

function ProjectGuard({ children }: { children: React.ReactNode }) {
  const { projectId } = useParams();
  const { data: project, isLoading, isError } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get(`/projects/${projectId}`).then(r => r.data),
    enabled: !!projectId,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-canvas-border border-t-gold" />
          <p className="text-xs text-text-muted">Loading deal...</p>
        </div>
      </div>
    );
  }

  if (isError || !project) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-risk-high/10 ring-1 ring-risk-high/20">
            <span className="text-risk-high text-xl">404</span>
          </div>
          <p className="text-sm font-medium text-text-primary">Deal not found</p>
          <p className="mt-1 text-xs text-text-muted">This deal does not exist or you don't have access.</p>
          <a href="/projects" className="mt-4 inline-flex items-center gap-1.5 text-xs text-gold hover:text-gold-light transition-colors font-medium">
            Back to Deals
          </a>
        </div>
      </div>
    );
  }

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
        <Route path="/projects/:projectId/documents" element={<ProjectGuard><DocumentsPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/planning" element={<ProjectGuard><PlanningPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/analysis" element={<ProjectGuard><AgentsPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/analysis/:runId" element={<ProjectGuard><AgentRunPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/finance" element={<ProjectGuard><FinancePage /></ProjectGuard>} />
        <Route path="/projects/:projectId/reports" element={<ProjectGuard><ReportsPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/red-flags" element={<ProjectGuard><RedFlagsPage /></ProjectGuard>} />
        <Route path="/projects/:projectId/settings" element={<ProjectGuard><ProjectSettingsPage /></ProjectGuard>} />
        <Route path="/admin/users" element={<RoleGuard allowedRoles={["admin"]}><AdminUsersPage /></RoleGuard>} />
        <Route path="/audit" element={<RoleGuard allowedRoles={["admin", "lead_advisor"]}><AuditLogsPage /></RoleGuard>} />
        <Route path="/settings" element={<SettingsPage />} />
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
