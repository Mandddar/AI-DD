import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { User, KeyRound, Shield, Trash2, CheckCircle, AlertCircle } from "lucide-react";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/auth";
import { cn } from "../lib/utils";

function StatusMessage({ type, message }: { type: "success" | "error"; message: string }) {
  return (
    <div className={cn(
      "flex items-center gap-2 rounded px-3 py-2 text-sm",
      type === "success" ? "bg-risk-low/10 text-risk-low" : "bg-risk-high/10 text-risk-high"
    )}>
      {type === "success" ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
      {message}
    </div>
  );
}

function PasswordSection() {
  const [current, setCurrent] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const mutation = useMutation({
    mutationFn: () => authApi.changePassword({ current_password: current, new_password: newPwd }),
    onSuccess: () => {
      setMsg({ type: "success", text: "Password changed successfully" });
      setCurrent(""); setNewPwd(""); setConfirm("");
    },
    onError: (err: any) => {
      setMsg({ type: "error", text: err.response?.data?.detail || "Failed to change password" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    if (newPwd !== confirm) {
      setMsg({ type: "error", text: "New passwords do not match" });
      return;
    }
    if (newPwd.length < 8) {
      setMsg({ type: "error", text: "Password must be at least 8 characters" });
      return;
    }
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {msg && <StatusMessage type={msg.type} message={msg.text} />}
      <div>
        <label className="label">Current Password</label>
        <input type="password" className="input w-full" value={current} onChange={(e) => setCurrent(e.target.value)} required />
      </div>
      <div>
        <label className="label">New Password</label>
        <input type="password" className="input w-full" value={newPwd} onChange={(e) => setNewPwd(e.target.value)} required />
      </div>
      <div>
        <label className="label">Confirm New Password</label>
        <input type="password" className="input w-full" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
      </div>
      <button type="submit" className="btn-primary px-4 py-2 text-sm" disabled={mutation.isPending}>
        {mutation.isPending ? "Changing…" : "Change Password"}
      </button>
    </form>
  );
}

function TwoFactorSection() {
  const { user, setUser } = useAuthStore();
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const setupMutation = useMutation({
    mutationFn: () => authApi.setup2FA(),
    onSuccess: (data) => { setSetup(data); setMsg(null); },
    onError: (err: any) => setMsg({ type: "error", text: err.response?.data?.detail || "Setup failed" }),
  });

  const verifyMutation = useMutation({
    mutationFn: () => authApi.verify2FA(code),
    onSuccess: () => {
      setMsg({ type: "success", text: "2FA enabled successfully" });
      setSetup(null);
      setCode("");
      if (user) setUser({ ...user, totp_enabled: true });
    },
    onError: (err: any) => setMsg({ type: "error", text: err.response?.data?.detail || "Verification failed" }),
  });

  const disableMutation = useMutation({
    mutationFn: () => authApi.disable2FA(),
    onSuccess: () => {
      setMsg({ type: "success", text: "2FA disabled" });
      if (user) setUser({ ...user, totp_enabled: false });
    },
    onError: (err: any) => setMsg({ type: "error", text: err.response?.data?.detail || "Failed to disable" }),
  });

  return (
    <div className="space-y-4">
      {msg && <StatusMessage type={msg.type} message={msg.text} />}

      {user?.totp_enabled ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-risk-low">
            <Shield size={14} /> Two-factor authentication is enabled
          </div>
          <button
            onClick={() => disableMutation.mutate()}
            className="btn-ghost px-4 py-2 text-sm text-risk-high hover:bg-risk-high/10"
            disabled={disableMutation.isPending}
          >
            Disable 2FA
          </button>
        </div>
      ) : setup ? (
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            Scan this secret in your authenticator app (Google Authenticator, Authy, etc.):
          </p>
          <div className="rounded bg-surface px-4 py-3">
            <p className="font-mono text-sm text-gold break-all">{setup.secret}</p>
          </div>
          <p className="text-xs text-text-muted">
            Or use this URI: <span className="font-mono text-text-secondary break-all">{setup.otpauth_uri}</span>
          </p>
          <div>
            <label className="label">Enter 6-digit code from your app</label>
            <div className="flex gap-2">
              <input
                type="text" className="input w-40" placeholder="000000"
                maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              />
              <button
                onClick={() => verifyMutation.mutate()}
                className="btn-primary px-4 py-2 text-sm"
                disabled={code.length !== 6 || verifyMutation.isPending}
              >
                Verify & Enable
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-text-secondary">
            Add an extra layer of security to your account with two-factor authentication.
          </p>
          <button
            onClick={() => setupMutation.mutate()}
            className="btn-primary px-4 py-2 text-sm"
            disabled={setupMutation.isPending}
          >
            {setupMutation.isPending ? "Setting up…" : "Set Up 2FA"}
          </button>
        </div>
      )}
    </div>
  );
}

function DangerZone() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();
  const [confirmText, setConfirmText] = useState("");

  const deleteMutation = useMutation({
    mutationFn: () => authApi.deleteAccount(),
    onSuccess: () => {
      logout();
      navigate("/login");
    },
  });

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">
        Permanently delete your account and all associated data. This action cannot be undone.
      </p>
      <div>
        <label className="label">Type "DELETE" to confirm</label>
        <input
          type="text" className="input w-60" placeholder="DELETE"
          value={confirmText} onChange={(e) => setConfirmText(e.target.value)}
        />
      </div>
      <button
        onClick={() => deleteMutation.mutate()}
        className="btn-danger px-4 py-2 text-sm"
        disabled={confirmText !== "DELETE" || deleteMutation.isPending}
      >
        {deleteMutation.isPending ? "Deleting…" : "Delete My Account"}
      </button>
    </div>
  );
}

export function SettingsPage() {
  const { user } = useAuthStore();

  const SECTIONS = [
    { id: "profile", icon: User, title: "Profile", description: "Your account information" },
    { id: "password", icon: KeyRound, title: "Password", description: "Change your password" },
    { id: "2fa", icon: Shield, title: "Two-Factor Authentication", description: "Secure your account with 2FA" },
    { id: "danger", icon: Trash2, title: "Danger Zone", description: "Delete your account" },
  ];

  return (
    <div className="animate-fade-in space-y-8 p-8 max-w-3xl">
      <div>
        <h1 className="font-display text-2xl font-semibold text-text-primary">Settings</h1>
        <p className="mt-1 text-sm text-text-secondary">Manage your account and security preferences</p>
      </div>

      {/* Profile Info (read-only) */}
      <section className="card p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-canvas-border pb-4">
          <User size={18} className="text-gold" />
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Profile</h2>
            <p className="text-xs text-text-muted">Your account information</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="label">Full Name</p>
            <p className="text-sm text-text-primary">{user?.full_name}</p>
          </div>
          <div>
            <p className="label">Email</p>
            <p className="text-sm text-text-primary">{user?.email}</p>
          </div>
          <div>
            <p className="label">Role</p>
            <p className="text-sm text-text-primary capitalize">{user?.role.replace("_", " ")}</p>
          </div>
          <div>
            <p className="label">Member Since</p>
            <p className="text-sm text-text-primary">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </p>
          </div>
        </div>
      </section>

      {/* Change Password */}
      <section className="card p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-canvas-border pb-4">
          <KeyRound size={18} className="text-gold" />
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Change Password</h2>
            <p className="text-xs text-text-muted">Update your password</p>
          </div>
        </div>
        <PasswordSection />
      </section>

      {/* 2FA */}
      <section className="card p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-canvas-border pb-4">
          <Shield size={18} className="text-gold" />
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Two-Factor Authentication</h2>
            <p className="text-xs text-text-muted">Secure your account with TOTP-based 2FA</p>
          </div>
        </div>
        <TwoFactorSection />
      </section>

      {/* Danger Zone */}
      <section className="card border-risk-high/20 p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-risk-high/20 pb-4">
          <Trash2 size={18} className="text-risk-high" />
          <div>
            <h2 className="text-sm font-semibold text-risk-high">Danger Zone</h2>
            <p className="text-xs text-text-muted">Irreversible actions</p>
          </div>
        </div>
        <DangerZone />
      </section>
    </div>
  );
}
