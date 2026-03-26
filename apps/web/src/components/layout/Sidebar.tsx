import { NavLink, useParams } from "react-router-dom";
import { LayoutDashboard, FolderOpen, FileText, Brain, BarChart3, Settings, LogOut } from "lucide-react";
import { useAuthStore } from "../../store/auth";
import { cn } from "../../lib/utils";

function useProjectNav() {
  const { projectId } = useParams<{ projectId?: string }>();
  return (path: string) => projectId ? `/projects/${projectId}${path}` : "/projects";
}

function SidebarContent() {
  const projectPath = useProjectNav();
  const { user, logout } = useAuthStore();

  const NAV = [
    { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", exact: false },
    { to: "/projects", icon: FolderOpen, label: "Deals", exact: false },
    { to: projectPath("/documents"), icon: FileText, label: "Documents", exact: false },
    { to: projectPath("/analysis"), icon: Brain, label: "AI Analysis", exact: false },
    { to: "/reports", icon: BarChart3, label: "Reports", exact: false },
  ];

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-canvas-border bg-canvas-subtle">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-canvas-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-gold/10 ring-1 ring-gold/30">
          <span className="font-display text-sm font-semibold text-gold">DD</span>
        </div>
        <div>
          <p className="font-display text-sm font-semibold text-text-primary tracking-wide">AI DD</p>
          <p className="text-[10px] text-text-muted uppercase tracking-widest">Due Diligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 p-3">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={label}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-gold/10 text-gold ring-1 ring-gold/20"
                  : "text-text-secondary hover:bg-surface hover:text-text-primary"
              )
            }
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + logout */}
      <div className="border-t border-canvas-border p-3 space-y-1">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 rounded px-3 py-2 text-sm text-text-secondary hover:bg-surface hover:text-text-primary transition-colors"
        >
          <Settings size={15} />
          Settings
        </NavLink>
        <div className="flex items-center gap-3 rounded px-3 py-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface text-xs font-medium text-text-secondary">
            {user?.full_name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-text-primary">{user?.full_name}</p>
            <p className="truncate text-[10px] text-text-muted capitalize">{user?.role.replace("_", " ")}</p>
          </div>
          <button onClick={logout} className="text-text-muted hover:text-text-secondary transition-colors">
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}

export function Sidebar() {
  return <SidebarContent />;
}
