import { useState } from 'react';
import { Settings, User, Shield, Save, Loader2 } from 'lucide-react';
import { useAuthStore } from '../../store/auth';
import { usePermissions } from '../../hooks/usePermissions';

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const perms = usePermissions();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6 space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <Settings className="w-7 h-7 text-gold" />
        <h1 className="text-2xl font-display font-bold text-text-primary">Settings</h1>
      </div>

      {/* Profile Section */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-5 h-5 text-gold" />
          <h2 className="text-lg font-display font-semibold text-text-primary">Profile</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input
              className="input w-full"
              value={user?.full_name ?? ''}
              disabled
            />
          </div>
          <div>
            <label className="label">Email</label>
            <input
              className="input w-full"
              value={user?.email ?? ''}
              disabled
            />
          </div>
          <div>
            <label className="label">Role</label>
            <input
              className="input w-full capitalize"
              value={user?.role.replace('_', ' ') ?? ''}
              disabled
            />
          </div>
          <div>
            <label className="label">Account Status</label>
            <input
              className="input w-full"
              value={user?.is_active ? 'Active' : 'Inactive'}
              disabled
            />
          </div>
        </div>

        <p className="text-xs text-text-muted">
          Contact your administrator to update your profile or role.
        </p>
      </div>

      {/* Security Section */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-5 h-5 text-gold" />
          <h2 className="text-lg font-display font-semibold text-text-primary">Security</h2>
        </div>

        <div>
          <label className="label">Change Password</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="input w-full" type="password" placeholder="Current password" />
            <input className="input w-full" type="password" placeholder="New password" />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-text-muted">
            Password must be at least 8 characters.
          </p>
          <button className="btn-primary px-4 py-2 text-sm flex items-center gap-2" onClick={handleSave}>
            {saved ? (
              <>
                <Loader2 className="w-4 h-4" /> Saved
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Permissions Overview */}
      <div className="card p-6">
        <h2 className="text-lg font-display font-semibold text-text-primary mb-4">Your Permissions</h2>
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
            <div key={label} className="flex items-center gap-2 text-sm">
              <span className={`h-2 w-2 rounded-full ${enabled ? 'bg-risk-low' : 'bg-text-muted/30'}`} />
              <span className={enabled ? 'text-text-primary' : 'text-text-muted'}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
