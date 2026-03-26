import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { authApi } from "../../api/auth";
import { useAuthStore } from "../../store/auth";

export function DisclaimerPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);

  const confirm = async () => {
    if (!accepted) return;
    setLoading(true);
    try {
      const user = await authApi.acceptDisclaimer();
      setUser(user);
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-lg animate-slide-in">
        <div className="card p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gold/10 ring-1 ring-gold/30">
              <ShieldAlert size={20} className="text-gold" />
            </div>
            <div>
              <h1 className="font-display text-lg text-text-primary">AI Disclaimer</h1>
              <p className="text-xs text-text-muted">Please read and accept before continuing</p>
            </div>
          </div>

          <div className="rounded-lg border border-canvas-border bg-canvas-subtle p-4 text-sm text-text-secondary leading-relaxed space-y-3">
            <p>
              This system uses <strong className="text-text-primary">Artificial Intelligence</strong> to support the
              due diligence review process.
            </p>
            <p>
              AI-generated results may be <strong className="text-risk-high">inaccurate, incomplete, or
              misleading</strong>. The AI works exclusively with uploaded documents and does not have access to
              external data sources.
            </p>
            <p>
              <strong className="text-text-primary">Responsibility</strong> for audit results, their interpretation,
              and all decisions derived therefrom lies exclusively with the human reviewer.
            </p>
            <p>
              This tool does <strong className="text-text-primary">not replace</strong> qualified legal, tax, or
              financial advisory services.
            </p>
          </div>

          <label className="mt-5 flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 accent-[#c9a84c]"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
            />
            <span className="text-sm text-text-secondary">
              I have read and understood the above disclaimer. I accept that AI-generated content requires
              human review and verification before use.
            </span>
          </label>

          <button
            onClick={confirm}
            disabled={!accepted || loading}
            className="btn-primary mt-5 w-full justify-center"
          >
            {loading ? "Confirming…" : "Accept & Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
