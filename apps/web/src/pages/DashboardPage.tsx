import { useQuery } from "@tanstack/react-query";
import { FolderOpen, FileSearch, AlertTriangle, CheckCircle } from "lucide-react";
import { projectsApi } from "../api/projects";
import { useAuthStore } from "../store/auth";
import { Link } from "react-router-dom";

const STAT_CARDS = [
  { label: "Active Deals", icon: FolderOpen, color: "text-gold", bg: "bg-gold/10", key: "active" },
  { label: "Documents Reviewed", icon: FileSearch, color: "text-risk-low", bg: "bg-risk-low/10", key: "docs" },
  { label: "Open Red Flags", icon: AlertTriangle, color: "text-risk-high", bg: "bg-risk-high/10", key: "flags" },
  { label: "Completed Deals", icon: CheckCircle, color: "text-risk-low", bg: "bg-risk-low/10", key: "completed" },
];

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  const active = projects.filter((p) => p.status === "active").length;
  const completed = projects.filter((p) => p.status === "completed").length;

  const stats: Record<string, number> = {
    active,
    docs: 0,
    flags: 0,
    completed,
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl text-text-primary">
          Welcome back, {user?.full_name.split(" ")[0]}
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          {new Date().toLocaleDateString("en-GB", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {STAT_CARDS.map(({ label, icon: Icon, color, bg, key }) => (
          <div key={key} className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-text-muted uppercase tracking-wider">{label}</span>
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${bg}`}>
                <Icon size={15} className={color} />
              </div>
            </div>
            <p className="text-2xl font-semibold text-text-primary">{stats[key]}</p>
          </div>
        ))}
      </div>

      {/* Recent deals */}
      <div className="card">
        <div className="flex items-center justify-between border-b border-canvas-border px-5 py-4">
          <h2 className="text-sm font-semibold text-text-primary">Recent Deals</h2>
          <Link to="/projects" className="text-xs text-gold hover:text-gold-light transition-colors">
            View all
          </Link>
        </div>
        {projects.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <FolderOpen size={32} className="mx-auto mb-3 text-text-muted" />
            <p className="text-sm text-text-secondary">No deals yet.</p>
            <Link to="/projects" className="mt-2 inline-block text-xs text-gold hover:text-gold-light transition-colors">
              Create your first deal →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-canvas-border">
            {projects.slice(0, 5).map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="flex items-center justify-between px-5 py-3.5 hover:bg-surface/50 transition-colors"
              >
                <div>
                  <p className="text-sm font-medium text-text-primary">{project.name}</p>
                  <p className="text-xs text-text-muted">
                    {project.company_name} · {project.legal_form} · {project.deal_type.replace("_", " ")}
                  </p>
                </div>
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    project.status === "active"
                      ? "bg-risk-low/10 text-risk-low"
                      : project.status === "completed"
                      ? "bg-gold/10 text-gold"
                      : "bg-surface text-text-muted"
                  }`}
                >
                  {project.status}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
