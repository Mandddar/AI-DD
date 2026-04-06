import { useState } from 'react';
import { Settings, User, Shield, Save, Loader2, Key, Trash2, Smartphone, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../../store/auth';
import { usePermissions } from '../../hooks/usePermissions';
import { authApi } from '../../api/auth';

export default function SettingsPage() {
  const { user, setUser, logout } = useAuthStore();
  const perms = usePermissions();

  // Profile
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState('');

  // Password
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [pwdSaving, setPwdSaving] = useState(false);
  const [pwdMsg, setPwdMsg] = useState('');

  // 2FA
  const [totpSecret, setTotpSecret] = useState('');
  const [totpUri, setTotpUri] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [totpSaving, setTotpSaving] = useState(false);
  const [totpMsg, setTotpMsg] = useState('');
  const [disablePwd, setDisablePwd] = useState('');

  // GDPR Deletion
  const [deletePwd, setDeletePwd] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState('');

  const handleProfileSave = async () => {
    setProfileSaving(true);
    setProfileMsg('');
    try {
      const updated = await authApi.updateProfile({
        full_name: fullName !== user?.full_name ? fullName : undefined,
        email: email !== user?.email ? email : undefined,
      });
      setUser(updated);
      setProfileMsg('Profile updated successfully.');
    } catch (err: any) {
      setProfileMsg(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setProfileSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    setPwdSaving(true);
    setPwdMsg('');
    try {
      await authApi.changePassword(currentPwd, newPwd);
      setPwdMsg('Password changed successfully.');
      setCurrentPwd('');
      setNewPwd('');
    } catch (err: any) {
      setPwdMsg(err.response?.data?.detail || 'Failed to change password.');
    } finally {
      setPwdSaving(false);
    }
  };

  const handleSetup2fa = async () => {
    setTotpSaving(true);
    setTotpMsg('');
    try {
      const result = await authApi.setup2fa();
      setTotpSecret(result.secret);
      setTotpUri(result.provisioning_uri);
      setTotpMsg('Scan the QR code with your authenticator app, then enter the code below.');
    } catch (err: any) {
      setTotpMsg(err.response?.data?.detail || 'Failed to setup 2FA.');
    } finally {
      setTotpSaving(false);
    }
  };

  const handleVerify2fa = async () => {
    setTotpSaving(true);
    try {
      const updated = await authApi.verify2fa(totpCode);
      setUser(updated);
      setTotpMsg('2FA enabled successfully!');
      setTotpSecret('');
      setTotpUri('');
      setTotpCode('');
    } catch (err: any) {
      setTotpMsg(err.response?.data?.detail || 'Invalid code. Try again.');
    } finally {
      setTotpSaving(false);
    }
  };

  const handleDisable2fa = async () => {
    setTotpSaving(true);
    try {
      const updated = await authApi.disable2fa(disablePwd);
      setUser(updated);
      setTotpMsg('2FA disabled.');
      setDisablePwd('');
    } catch (err: any) {
      setTotpMsg(err.response?.data?.detail || 'Failed to disable 2FA.');
    } finally {
      setTotpSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== 'DELETE MY ACCOUNT') {
      setDeleteMsg('Please type "DELETE MY ACCOUNT" to confirm.');
      return;
    }
    setDeleting(true);
    setDeleteMsg('');
    try {
      await authApi.deleteAccount(deletePwd);
      logout();
      window.location.href = '/login';
    } catch (err: any) {
      setDeleteMsg(err.response?.data?.detail || 'Failed to delete account.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <Settings className="w-8 h-8 text-gold" />
        <h1 className="text-3xl font-display font-bold text-text-primary">Settings</h1>
      </div>

      {/* Profile Section */}
      <div className="card p-7 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-6 h-6 text-gold" />
          <h2 className="text-xl font-display font-semibold text-text-primary">Profile</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input className="input w-full" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input w-full" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label">Role</label>
            <input className="input w-full capitalize" value={user?.role.replace('_', ' ') ?? ''} disabled />
          </div>
          <div>
            <label className="label">Account Status</label>
            <input className="input w-full" value={user?.is_active ? 'Active' : 'Inactive'} disabled />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          {profileMsg && <p className={`text-sm ${profileMsg.includes('success') ? 'text-risk-low' : 'text-risk-high'}`}>{profileMsg}</p>}
          <button
            className="btn-primary px-4 py-2 text-base flex items-center gap-2 ml-auto"
            onClick={handleProfileSave}
            disabled={profileSaving}
          >
            {profileSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Profile
          </button>
        </div>
      </div>

      {/* Security — Password Change */}
      <div className="card p-7 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Key className="w-6 h-6 text-gold" />
          <h2 className="text-xl font-display font-semibold text-text-primary">Change Password</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            className="input w-full"
            type="password"
            placeholder="Current password"
            value={currentPwd}
            onChange={(e) => setCurrentPwd(e.target.value)}
          />
          <input
            className="input w-full"
            type="password"
            placeholder="New password (min 8 chars)"
            value={newPwd}
            onChange={(e) => setNewPwd(e.target.value)}
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          {pwdMsg && <p className={`text-sm ${pwdMsg.includes('success') ? 'text-risk-low' : 'text-risk-high'}`}>{pwdMsg}</p>}
          <button
            className="btn-primary px-4 py-2 text-base flex items-center gap-2 ml-auto"
            onClick={handlePasswordChange}
            disabled={pwdSaving || !currentPwd || newPwd.length < 8}
          >
            {pwdSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
            Change Password
          </button>
        </div>
      </div>

      {/* 2FA / TOTP */}
      <div className="card p-7 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Smartphone className="w-6 h-6 text-gold" />
          <h2 className="text-xl font-display font-semibold text-text-primary">Two-Factor Authentication</h2>
          {user?.totp_enabled && (
            <span className="ml-2 inline-flex items-center rounded-full bg-risk-low/10 px-2 py-0.5 text-sm font-medium text-risk-low">
              Enabled
            </span>
          )}
        </div>

        <p className="text-base text-text-secondary">
          {user?.totp_enabled
            ? 'Two-factor authentication is active. Your account is protected with an authenticator app.'
            : 'Add an extra layer of security by enabling two-factor authentication with an authenticator app (e.g., Google Authenticator, Authy).'}
        </p>

        {!user?.totp_enabled ? (
          <>
            {totpSecret ? (
              <div className="space-y-3">
                <div className="bg-surface rounded-lg border border-canvas-border p-5">
                  <p className="text-sm text-text-muted mb-2">Manual entry key:</p>
                  <code className="text-base text-gold font-mono break-all">{totpSecret}</code>
                </div>
                <div className="bg-surface rounded-lg border border-canvas-border p-5">
                  <p className="text-sm text-text-muted mb-2">Provisioning URI (paste in authenticator):</p>
                  <code className="text-sm text-text-secondary font-mono break-all">{totpUri}</code>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    className="input w-48"
                    placeholder="6-digit code"
                    maxLength={6}
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                  />
                  <button
                    className="btn-primary px-4 py-2 text-base"
                    onClick={handleVerify2fa}
                    disabled={totpSaving || totpCode.length !== 6}
                  >
                    {totpSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify & Enable'}
                  </button>
                </div>
              </div>
            ) : (
              <button
                className="btn-primary px-4 py-2 text-base flex items-center gap-2"
                onClick={handleSetup2fa}
                disabled={totpSaving}
              >
                {totpSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Smartphone className="w-4 h-4" />}
                Setup 2FA
              </button>
            )}
          </>
        ) : (
          <div className="flex items-center gap-3">
            <input
              className="input w-48"
              type="password"
              placeholder="Enter password to disable"
              value={disablePwd}
              onChange={(e) => setDisablePwd(e.target.value)}
            />
            <button
              className="btn-danger px-4 py-2 text-base"
              onClick={handleDisable2fa}
              disabled={totpSaving || !disablePwd}
            >
              {totpSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Disable 2FA'}
            </button>
          </div>
        )}

        {totpMsg && <p className={`text-sm ${totpMsg.includes('success') || totpMsg.includes('enabled') ? 'text-risk-low' : 'text-text-secondary'}`}>{totpMsg}</p>}
      </div>

      {/* Permissions Overview */}
      <div className="card p-7">
        <h2 className="text-xl font-display font-semibold text-text-primary mb-4">Your Permissions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { label: 'Create Deals', enabled: perms.canCreateProject },
            { label: 'Upload Documents', enabled: perms.canUploadDocuments },
            { label: 'Run AI Analysis', enabled: perms.canRunAnalysis },
            { label: 'Manage Reports', enabled: perms.canManageReports },
            { label: 'View Reports', enabled: perms.canViewReports },
            { label: 'View Audit Trail', enabled: perms.canViewAudit },
            { label: 'Manage Planning', enabled: perms.canManagePlanning },
            { label: 'Finance Analysis', enabled: perms.canRunFinanceAnalysis },
            { label: 'Review Findings', enabled: perms.canReviewFindings },
          ].map(({ label, enabled }) => (
            <div key={label} className="flex items-center gap-2 text-base">
              <span className={`h-2 w-2 rounded-full ${enabled ? 'bg-risk-low' : 'bg-text-muted/30'}`} />
              <span className={enabled ? 'text-text-primary' : 'text-text-muted'}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* GDPR Account Deletion */}
      <div className="card p-7 space-y-4 border-risk-high/20">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-6 h-6 text-risk-high" />
          <h2 className="text-xl font-display font-semibold text-risk-high">Delete Account</h2>
        </div>

        <p className="text-base text-text-secondary">
          Permanently delete your account and anonymize all associated data per GDPR Article 17.
          This action cannot be undone.
        </p>

        <div className="space-y-3">
          <input
            className="input w-full"
            type="password"
            placeholder="Enter your password"
            value={deletePwd}
            onChange={(e) => setDeletePwd(e.target.value)}
          />
          <input
            className="input w-full"
            placeholder='Type "DELETE MY ACCOUNT" to confirm'
            value={deleteConfirm}
            onChange={(e) => setDeleteConfirm(e.target.value)}
          />
          <button
            className="btn-danger px-4 py-2 text-base flex items-center gap-2"
            onClick={handleDeleteAccount}
            disabled={deleting || !deletePwd || deleteConfirm !== 'DELETE MY ACCOUNT'}
          >
            {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            Permanently Delete Account
          </button>
          {deleteMsg && <p className="text-sm text-risk-high">{deleteMsg}</p>}
        </div>
      </div>
    </div>
  );
}
