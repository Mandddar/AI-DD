import { NavLink, useParams } from "react-router-dom";
import {
  LayoutDashboard, FolderOpen, FileText, Brain, BarChart3,
  ClipboardList, TrendingUp, Shield, Settings, LogOut, Lock, AlertTriangle, Users
} from "lucide-react";
import { useAuthStore } from "../../store/auth";
import { usePermissions } from "../../hooks/usePermissions";
import { cn } from "../../lib/utils";

function SidebarContent() {
  const { projectId } = useParams<{ projectId?: string }>();
  const { user, logout } = useAuthStore();
  const perms = usePermissions();

  // Build project links — show all standard items but disable those the role can't access
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

  // Split into sections: first 2 are "General", system items (admin/audit), rest is "Project"
  const generalItems = NAV.slice(0, 2);
  const systemPaths = ["/audit", "/admin/users"];
  const systemItems = NAV.filter(i => systemPaths.includes(i.to));
  const projectItems = NAV.filter(i => !generalItems.includes(i) && !systemItems.includes(i));

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
      <nav className="flex-1 space-y-0.5 p-3 overflow-y-auto">
        {projectId && (
          <p className="px-3 pt-2 pb-1 text-[10px] text-text-muted uppercase tracking-widest">General</p>
        )}
        {generalItems.map((item) => (
          <NavItem key={item.label} item={item} />
        ))}

        {projectId && projectItems.length > 0 && (
          <p className="px-3 pt-4 pb-1 text-[10px] text-text-muted uppercase tracking-widest">Project</p>
        )}
        {projectItems.map((item) => (
          <NavItem key={item.label} item={item} />
        ))}

        {systemItems.length > 0 && (
          <p className="px-3 pt-4 pb-1 text-[10px] text-text-muted uppercase tracking-widest">System</p>
        )}
        {systemItems.map((item) => (
          <NavItem key={item.label} item={item} />
        ))}
      </nav>

      {/* User + actions */}
      <div className="border-t border-canvas-border p-3 space-y-1">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-gold/10 text-gold ring-1 ring-gold/20"
                : "text-text-secondary hover:bg-surface hover:text-text-primary"
            )
          }
        >
          <Settings size={15} />
          Settings
        </NavLink>
        <div className="flex items-center gap-3 rounded px-3 py-2">
          <NavLink to="/settings" className="flex items-center gap-3 min-w-0 flex-1 group" title="View profile & settings">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface text-xs font-medium text-text-secondary group-hover:bg-gold/10 group-hover:text-gold transition-colors">
              {user?.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-text-primary group-hover:text-gold transition-colors">{user?.full_name}</p>
              <p className="truncate text-[10px] text-text-muted capitalize">{user?.role.replace("_", " ")}</p>
            </div>
          </NavLink>
          <button
            onClick={logout}
            title="Sign Out"
            className="text-text-muted hover:text-risk-high transition-colors p-1 rounded hover:bg-risk-high/10"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}

function NavItem({ item }: { item: any }) {
  const Icon = item.icon;
  const disabled = "disabled" in item && item.disabled;

  if (disabled) {
    return (
      <span
        className="flex items-center gap-3 rounded px-3 py-2 text-sm text-text-muted/50 cursor-not-allowed group/disabled"
        title={item.tip || "Select a deal to access this feature"}
      >
        <Icon size={15} />
        <span className="flex-1">{item.label}</span>
        <Lock size={12} className="opacity-40" />
      </span>
    );
  }

  return (
    <NavLink
      to={item.to}
      end={item.end}
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
      {item.label}
    </NavLink>
  );
}

export function Sidebar() {
  return <SidebarContent />;
}
