import { NavLink, useParams } from "react-router-dom";
import {
  LayoutDashboard, FolderOpen, FileText, Brain, BarChart3,
  ClipboardList, TrendingUp, Shield, Settings, LogOut, Lock, AlertTriangle, Users,
} from "lucide-react";
import { useAuthStore } from "../../store/auth";
import { usePermissions } from "../../hooks/usePermissions";
import { ThemeToggle } from "../ThemeToggle";
import { cn } from "../../lib/utils";

interface SidebarProps {
  onNavigate?: () => void;
}

function SidebarContent({ onNavigate }: SidebarProps) {
  const { projectId } = useParams<{ projectId?: string }>();
  const { user, logout } = useAuthStore();
  const perms = usePermissions();

  const allProjectLinks = projectId
    ? [
        { to: `/projects/${projectId}/documents`, icon: FileText, label: "Documents", show: true },
        { to: perms.canViewPlanning ? `/projects/${projectId}/planning` : "#", icon: ClipboardList, label: "Planning", show: true, disabled: !perms.canViewPlanning },
        { to: perms.isAdvisor ? `/projects/${projectId}/analysis` : "#", icon: Brain, label: "AI Analysis", show: true, disabled: !perms.isAdvisor },
        { to: perms.isAdvisor ? `/projects/${projectId}/red-flags` : "#", icon: AlertTriangle, label: "Red Flags", show: perms.isAdvisor },
        { to: !perms.isReadOnly ? `/projects/${projectId}/finance` : "#", icon: TrendingUp, label: "Finance", show: true, disabled: perms.isReadOnly },
        { to: `/projects/${projectId}/reports`, icon: BarChart3, label: "Reports", show: perms.canViewReports },
        { to: `/projects/${projectId}/settings`, icon: Settings, label: "Deal Settings", show: perms.canManageProject },
      ]
    : [
        { to: "#", icon: FileText, label: "Documents", disabled: true, show: true, tip: "Select a deal to view documents" },
        { to: "#", icon: ClipboardList, label: "Planning", disabled: true, show: true, tip: perms.canViewPlanning ? "Select a deal first" : "Not available for your role" },
        { to: "#", icon: Brain, label: "AI Analysis", disabled: true, show: true, tip: perms.isAdvisor ? "Select a deal first" : "Not available for your role" },
        { to: "#", icon: AlertTriangle, label: "Red Flags", disabled: true, show: perms.isAdvisor, tip: "Select a deal first" },
        { to: "#", icon: TrendingUp, label: "Finance", disabled: true, show: true, tip: !perms.isReadOnly ? "Select a deal first" : "Not available for your role" },
        { to: "#", icon: BarChart3, label: "Reports", disabled: true, show: perms.canViewReports, tip: "Select a deal first" },
      ];

  const projectLinks = allProjectLinks.filter(l => l.show);

  const NAV = [
    { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", end: true, show: true },
    { to: "/projects", icon: FolderOpen, label: "Deals", end: true, show: true },
    ...projectLinks.map(l => ({ ...l, end: false })),
    { to: "/admin/users", icon: Users, label: "Team Management", end: true, show: perms.role === "admin" },
    { to: "/audit", icon: Shield, label: "Audit Trail", end: true, show: perms.canViewAudit },
  ].filter(item => item.show);

  const generalItems = NAV.slice(0, 2);
  const systemPaths = ["/audit", "/admin/users"];
  const systemItems = NAV.filter(i => systemPaths.includes(i.to));
  const projectItems = NAV.filter(i => !generalItems.includes(i) && !systemItems.includes(i));

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-canvas-border bg-canvas-subtle">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3.5 border-b border-canvas-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold/10 ring-1 ring-gold/25">
          <span className="font-display text-base font-semibold text-gold">DD</span>
        </div>
        <div>
          <p className="font-display text-base font-semibold text-text-primary tracking-wide">AI DD</p>
          <p className="text-[11px] text-text-muted uppercase tracking-[0.15em]">Due Diligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {projectId && (
          <p className="px-3 pt-1 pb-2 text-[11px] text-text-muted uppercase tracking-[0.15em] font-medium">General</p>
        )}
        {generalItems.map((item) => (
          <NavItem key={item.label} item={item} onNavigate={onNavigate} />
        ))}

        {projectId && projectItems.length > 0 && (
          <p className="px-3 pt-5 pb-2 text-[11px] text-text-muted uppercase tracking-[0.15em] font-medium">Project</p>
        )}
        {projectItems.map((item) => (
          <NavItem key={item.label} item={item} onNavigate={onNavigate} />
        ))}

        {systemItems.length > 0 && (
          <p className="px-3 pt-5 pb-2 text-[11px] text-text-muted uppercase tracking-[0.15em] font-medium">System</p>
        )}
        {systemItems.map((item) => (
          <NavItem key={item.label} item={item} onNavigate={onNavigate} />
        ))}
      </nav>

      {/* Theme + User */}
      <div className="border-t border-canvas-border p-3 space-y-2">
        <div className="flex items-center justify-between px-3.5 py-1.5">
          <span className="text-xs text-text-muted font-medium">Theme</span>
          <ThemeToggle />
        </div>

        <NavLink
          to="/settings"
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm transition-all duration-200",
              isActive
                ? "bg-gold/10 text-gold ring-1 ring-gold/20"
                : "text-text-secondary hover:bg-surface hover:text-text-primary"
            )
          }
        >
          <Settings size={16} />
          Settings
        </NavLink>
        <div className="flex items-center gap-3 rounded-lg px-3.5 py-2.5">
          <NavLink to="/settings" onClick={onNavigate} className="flex items-center gap-3 min-w-0 flex-1 group" title="View profile & settings">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface text-xs font-semibold text-text-secondary group-hover:bg-gold/10 group-hover:text-gold transition-all duration-200">
              {user?.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary group-hover:text-gold transition-colors">{user?.full_name}</p>
              <p className="truncate text-xs text-text-muted capitalize">{user?.role.replace("_", " ")}</p>
            </div>
          </NavLink>
          <button
            onClick={logout}
            title="Sign Out"
            className="text-text-muted hover:text-risk-high transition-all duration-200 p-1.5 rounded-lg hover:bg-risk-high/10"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}

function NavItem({ item, onNavigate }: { item: any; onNavigate?: () => void }) {
  const Icon = item.icon;
  const disabled = "disabled" in item && item.disabled;

  if (disabled) {
    return (
      <span
        className="flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm text-text-muted/40 cursor-not-allowed"
        title={item.tip || "Select a deal to access this feature"}
      >
        <Icon size={16} />
        <span className="flex-1">{item.label}</span>
        <Lock size={13} className="opacity-30" />
      </span>
    );
  }

  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-gold/10 text-gold ring-1 ring-gold/20"
            : "text-text-secondary hover:bg-surface hover:text-text-primary"
        )
      }
    >
      <Icon size={16} />
      {item.label}
    </NavLink>
  );
}

export function Sidebar({ onNavigate }: SidebarProps = {}) {
  return <SidebarContent onNavigate={onNavigate} />;
}
