import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  FolderOpen,
  FileSearch,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  TrendingUp,
  Clock,
  ChevronRight,
} from "lucide-react";
import { projectsApi } from "../api/projects";
import { useAuthStore } from "../store/auth";
import { usePermissions } from "../hooks/usePermissions";
import { Link } from "react-router-dom";

const DEAL_TYPE_LABELS: Record<string, string> = {
  share_deal: "Share Deal",
  asset_deal: "Asset Deal",
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const perms = usePermissions();
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  const active = projects.filter((p) => p.status === "active").length;
  const completed = projects.filter((p) => p.status === "completed").length;
  const firstName = user?.full_name.split(" ")[0] ?? "";

  const stats = useMemo(
    () => [
      {
        label: "Active Deals",
        value: active,
        icon: FolderOpen,
        color: "text-gold",
        bg: "bg-gold/10",
        ring: "ring-gold/20",
        trend: active > 0 ? `${active} in progress` : "No active deals",
      },
      {
        label: "Documents Reviewed",
        value: 0,
        icon: FileSearch,
        color: "text-risk-low",
        bg: "bg-risk-low/10",
        ring: "ring-risk-low/20",
        trend: "Across all deals",
      },
      {
        label: "Open Red Flags",
        value: 0,
        icon: AlertTriangle,
        color: "text-risk-high",
        bg: "bg-risk-high/10",
        ring: "ring-risk-high/20",
        trend: "Pending review",
      },
      {
        label: "Completed Deals",
        value: completed,
        icon: CheckCircle,
        color: "text-risk-low",
        bg: "bg-risk-low/10",
        ring: "ring-risk-low/20",
        trend: completed > 0 ? `${completed} closed` : "None yet",
      },
    ],
    [active, completed],
  );

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">
            {greeting()}, {firstName}
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            {new Date().toLocaleDateString("en-GB", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>
        {perms.canCreateProject && (
          <Link to="/projects" className="btn-primary text-sm gap-1.5">
            New deal <ArrowRight size={13} />
          </Link>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, color, bg, ring, trend }) => (
          <div key={label} className="card p-5 group hover:border-canvas-border/80 transition-all">
            <div className="flex items-start justify-between mb-4">
              <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${bg} ring-1 ${ring}`}>
                <Icon size={16} className={color} />
              </div>
              <TrendingUp size={12} className="text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="font-display text-3xl text-text-primary">{value}</p>
            <p className="mt-1 text-xs text-text-muted uppercase tracking-wider">{label}</p>
            <p className="mt-2 text-xs text-text-secondary border-t border-canvas-border pt-2">{trend}</p>
          </div>
        ))}
      </div>

      <div className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-canvas-border px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Recent Deals</h2>
            <p className="text-xs text-text-muted mt-0.5">Your latest active mandates</p>
          </div>
          <Link
            to="/projects"
            className="flex items-center gap-1 text-xs text-gold hover:text-gold-light transition-colors"
          >
            View all <ArrowRight size={12} />
          </Link>
        </div>

        {isLoading ? (
          <div className="px-5 py-10 text-center">
            <div className="mx-auto h-5 w-5 animate-spin rounded-full border-2 border-canvas-border border-t-gold mb-3" />
            <p className="text-xs text-text-muted">Loading deals…</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="px-5 py-14 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold/5 ring-1 ring-gold/20">
              <FolderOpen size={24} className="text-gold/60" />
            </div>
            <p className="text-sm font-medium text-text-primary">No deals yet</p>
            <p className="mt-1 text-xs text-text-muted">Create your first deal to get started.</p>
            <Link
              to="/projects"
              className="mt-4 inline-flex items-center gap-1.5 text-xs text-gold hover:text-gold-light transition-colors font-medium"
            >
              Create your first deal <ArrowRight size={12} />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-canvas-border">
            {projects.slice(0, 6).map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}/documents`}
                className="group flex items-center justify-between px-5 py-4 hover:bg-surface/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-canvas-subtle ring-1 ring-canvas-border">
                    <span className="text-xs font-semibold text-text-secondary">
                      {project.company_name?.slice(0, 2).toUpperCase() ?? "??"}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary group-hover:text-gold transition-colors">
                      {project.name}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <p className="text-xs text-text-muted">{project.company_name}</p>
                      <span className="text-text-muted/40">·</span>
                      <p className="text-xs text-text-muted">{project.legal_form}</p>
                      <span className="text-text-muted/40">·</span>
                      <p className="text-xs text-text-muted">
                        {DEAL_TYPE_LABELS[project.deal_type] ?? project.deal_type}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      project.status === "active"
                        ? "bg-risk-low/10 text-risk-low"
                        : project.status === "completed"
                        ? "bg-gold/10 text-gold"
                        : "bg-surface text-text-muted"
                    }`}
                  >
                    {project.status === "active" && (
                      <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-risk-low inline-block" />
                    )}
                    {project.status}
                  </span>
                  <ChevronRight size={14} className="text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {projects.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              icon: FolderOpen,
              label: "All Deals",
              sub: "Manage your pipeline",
              to: "/projects",
              color: "text-gold",
              bg: "bg-gold/10",
            },
            {
              icon: FileSearch,
              label: "Upload Documents",
              sub: "Add files to a deal",
              to: `/projects/${projects[0]?.id}/documents`,
              color: "text-risk-low",
              bg: "bg-risk-low/10",
            },
            {
              icon: Clock,
              label: "Run Analysis",
              sub: "Start AI agent review",
              to: `/projects/${projects[0]?.id}/analysis`,
              color: "text-text-secondary",
              bg: "bg-surface",
            },
          ].map(({ icon: Icon, label, sub, to, color, bg }) => (
            <Link
              key={label}
              to={to}
              className="card p-4 flex items-center gap-3 hover:border-canvas-border/80 transition-all group"
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${bg}`}>
                <Icon size={16} className={color} />
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary group-hover:text-gold transition-colors">{label}</p>
                <p className="text-xs text-text-muted">{sub}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
