import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Mail, Key, Loader2, CheckCircle } from "lucide-react";
import { authApi } from "../../api/auth";
import { ThemeToggle } from "../../components/ThemeToggle";

export function ForgotPasswordPage() {
  const [step, setStep] = useState<"request" | "confirm" | "done">("request");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [devToken, setDevToken] = useState("");

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await authApi.requestPasswordReset(email);
      if (result.reset_token) {
        setDevToken(result.reset_token);
        setToken(result.reset_token);
      }
      setStep("confirm");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to request reset.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      setStep("done");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 sm:px-6 py-12">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex items-center justify-between mb-8">
          <Link to="/login" className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors">
            <ArrowLeft size={16} /> Back to login
          </Link>
          <ThemeToggle />
        </div>

        {step === "request" && (
          <>
            <div className="mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold/10 ring-1 ring-gold/30 mb-4">
                <Mail size={22} className="text-gold" />
              </div>
              <h2 className="font-display text-2xl sm:text-3xl text-text-primary">Reset Password</h2>
              <p className="mt-1 text-base text-text-secondary">
                Enter your email address and we'll generate a reset token.
              </p>
            </div>

            <form onSubmit={handleRequest} className="space-y-4">
              <div>
                <label className="label">Email address</label>
                <input
                  className="input w-full"
                  type="email"
                  placeholder="advisor@firm.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              {error && <p className="text-sm text-risk-high">{error}</p>}
              <button type="submit" disabled={loading} className="btn-primary w-full justify-center">
                {loading ? <Loader2 size={18} className="animate-spin" /> : "Send Reset Token"}
              </button>
            </form>
          </>
        )}

        {step === "confirm" && (
          <>
            <div className="mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold/10 ring-1 ring-gold/30 mb-4">
                <Key size={22} className="text-gold" />
              </div>
              <h2 className="font-display text-2xl sm:text-3xl text-text-primary">Enter New Password</h2>
              <p className="mt-1 text-base text-text-secondary">
                {devToken
                  ? "Dev mode: your reset token has been auto-filled below."
                  : "Enter the reset token you received and your new password."}
              </p>
            </div>

            <form onSubmit={handleConfirm} className="space-y-4">
              <div>
                <label className="label">Reset Token</label>
                <input
                  className="input w-full font-mono text-sm"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">New Password</label>
                <input
                  className="input w-full"
                  type="password"
                  placeholder="At least 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              {error && <p className="text-sm text-risk-high">{error}</p>}
              <button type="submit" disabled={loading || newPassword.length < 8} className="btn-primary w-full justify-center">
                {loading ? <Loader2 size={18} className="animate-spin" /> : "Reset Password"}
              </button>
            </form>
          </>
        )}

        {step === "done" && (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-risk-low/10 ring-1 ring-risk-low/20">
              <CheckCircle size={28} className="text-risk-low" />
            </div>
            <h2 className="font-display text-2xl sm:text-3xl text-text-primary">Password Reset</h2>
            <p className="mt-2 text-base text-text-secondary">
              Your password has been reset successfully. You can now sign in.
            </p>
            <Link to="/login" className="btn-primary inline-flex mt-6 px-6 py-2">
              Go to Login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
