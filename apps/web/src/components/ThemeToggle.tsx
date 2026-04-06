import { Sun, Moon, Monitor } from "lucide-react";
import { useThemeStore } from "../store/theme";
import { cn } from "../lib/utils";

type Variant = "compact" | "pills";

/**
 * Theme toggle - reusable across sidebar, navbar, auth pages.
 *
 * variant="compact"  → small icon-only row (sidebar / navbar)
 * variant="pills"    → labeled pill buttons (settings page)
 */
export function ThemeToggle({ variant = "compact" }: { variant?: Variant }) {
  const { theme, setTheme } = useThemeStore();

  const options = [
    { value: "light" as const, icon: Sun, label: "Light" },
    { value: "dark" as const, icon: Moon, label: "Dark" },
    { value: "system" as const, icon: Monitor, label: "Auto" },
  ];

  if (variant === "pills") {
    return (
      <div className="inline-flex items-center gap-1 rounded-xl bg-surface p-1">
        {options.map(({ value, icon: Icon, label }) => (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={cn(
              "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200",
              theme === value
                ? "bg-canvas-card text-gold shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>
    );
  }

  // compact: icon-only
  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-surface p-1">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          title={label}
          className={cn(
            "flex items-center justify-center rounded-md p-1.5 transition-all duration-200",
            theme === value
              ? "bg-canvas-card text-gold shadow-sm"
              : "text-text-muted hover:text-text-secondary"
          )}
        >
          <Icon size={14} />
        </button>
      ))}
    </div>
  );
}
