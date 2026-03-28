import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ShieldCheck, FileSearch, BarChart3 } from "lucide-react";
import { authApi } from "../../api/auth";
import { useAuthStore } from "../../store/auth";

const SELLING_POINTS = [
  { icon: FileSearch, text: "Automated document review across all workstreams" },
  { icon: ShieldCheck, text: "AI red-flag detection in minutes, not days" },
  { icon: BarChart3, text: "Risk scoring with full reviewer audit trail" },
];

export function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await authApi.login(form);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      const user = await authApi.me();
      setUser(user);
      navigate(user.disclaimer_accepted ? "/dashboard" : "/disclaimer");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-canvas">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[520px] shrink-0 flex-col justify-between border-r border-canvas-border bg-canvas-subtle p-10">
        <Link to="/" className="flex items-center gap-2 text-text-muted hover:text-text-primary transition-colors text-sm">
          <ArrowLeft size={14} /> Back to home
        </Link>

        <div>
          {/* Logo */}
          <div className="mb-10">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold/10 ring-1 ring-gold/30 mb-4">
              <span className="font-display text-xl font-semibold text-gold">DD</span>
            </div>
            <h1 className="font-display text-3xl text-text-primary leading-snug">
              The intelligent<br />due diligence platform.
            </h1>
            <p className="mt-3 text-sm text-text-secondary leading-relaxed">
              Purpose-built for M&A advisors who need to move fast without missing the details that matter.
            </p>
          </div>

          <div className="space-y-4">
            {SELLING_POINTS.map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gold/10">
                  <Icon size={14} className="text-gold" />
                </div>
                <p className="text-sm text-text-secondary">{text}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-text-muted">© {new Date().getFullYear()} AI DD · M&A Due Diligence Platform</p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Mobile logo */}
          <div className="mb-8 text-center lg:hidden">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gold/10 ring-1 ring-gold/30">
              <span className="font-display text-base font-semibold text-gold">DD</span>
            </div>
            <h1 className="font-display text-xl text-text-primary">AI DD</h1>
          </div>

          <div>
            <h2 className="font-display text-2xl text-text-primary">Welcome back</h2>
            <p className="mt-1 text-sm text-text-secondary">Sign in to your account to continue.</p>
          </div>

          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label className="label">Email address</label>
              <input
                className="input"
                type="email"
                placeholder="advisor@firm.com"
                value={form.email}
                onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                className="input"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
            </div>

            {error && (
              <div className="rounded-lg border border-risk-high/20 bg-risk-high/5 px-3 py-2.5">
                <p className="text-xs text-risk-high">{error}</p>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-2">
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-canvas border-t-canvas/30" />
                  Signing in…
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-text-muted">
            Don't have an account?{" "}
            <Link to="/register" className="text-gold hover:text-gold-light transition-colors font-medium">
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
