import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, UserPlus, Loader2, Users, Trash2 } from 'lucide-react';
import { api } from '../../api/client';
import { projectsApi } from '../../api/projects';
import { usePermissions } from '../../hooks/usePermissions';

export default function ProjectSettingsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const perms = usePermissions();
  const [email, setEmail] = useState('');
  const [addError, setAddError] = useState('');

  const { data: project, isLoading: loadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
  });

  const addMember = useMutation({
    mutationFn: (userEmail: string) =>
      api.post(`/projects/${projectId}/members`, { user_email: userEmail }).then(r => r.data),
    onSuccess: () => {
      setEmail('');
      setAddError('');
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
    onError: (err: any) => {
      setAddError(err?.response?.data?.detail || 'Failed to add member');
    },
  });

  if (loadingProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <Settings className="w-7 h-7 text-gold" />
        <div>
          <h1 className="text-2xl font-display font-bold text-text-primary">Deal Settings</h1>
          <p className="text-sm text-text-secondary mt-0.5">{project?.name}</p>
        </div>
      </div>

      {/* Deal Info */}
      <div className="card p-6">
        <h2 className="text-lg font-display font-semibold text-text-primary mb-4">Deal Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-text-muted">Company</span>
            <p className="text-text-primary font-medium">{project?.company_name}</p>
          </div>
          <div>
            <span className="text-text-muted">Legal Form</span>
            <p className="text-text-primary font-medium">{project?.legal_form}</p>
          </div>
          <div>
            <span className="text-text-muted">Deal Type</span>
            <p className="text-text-primary font-medium capitalize">{project?.deal_type?.replace('_', ' ')}</p>
          </div>
          <div>
            <span className="text-text-muted">Industry</span>
            <p className="text-text-primary font-medium">{project?.industry || '—'}</p>
          </div>
          <div>
            <span className="text-text-muted">Status</span>
            <p className="text-text-primary font-medium capitalize">{project?.status}</p>
          </div>
          <div>
            <span className="text-text-muted">Created</span>
            <p className="text-text-primary font-medium">{project?.created_at ? new Date(project.created_at).toLocaleDateString() : '—'}</p>
          </div>
        </div>
      </div>

      {/* Add Member */}
      {perms.canManageProject && (
        <div className="card p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-gold" />
            <h2 className="text-lg font-display font-semibold text-text-primary">Team Members</h2>
          </div>
          <p className="text-text-secondary text-sm">
            Add users to this deal by their email address. They must have a registered account.
          </p>
          <div className="flex gap-3">
            <input
              className="input flex-1"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={e => { setEmail(e.target.value); setAddError(''); }}
            />
            <button
              className="btn-primary px-4 py-2 flex items-center gap-2 text-sm"
              disabled={!email.trim() || addMember.isPending}
              onClick={() => addMember.mutate(email.trim())}
            >
              <UserPlus size={14} />
              {addMember.isPending ? 'Adding...' : 'Add Member'}
            </button>
          </div>
          {addError && (
            <p className="text-xs text-risk-high bg-risk-high/10 rounded px-3 py-2">{addError}</p>
          )}
          {addMember.isSuccess && (
            <p className="text-xs text-risk-low bg-risk-low/10 rounded px-3 py-2">Member added successfully.</p>
          )}
        </div>
      )}

      {/* Data Room Controls */}
      {perms.canManageProject && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-text-primary">Data Room Controls</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-sm text-text-primary font-medium">NDA Required</p>
                <p className="text-xs text-text-muted">Users must accept NDA before accessing documents</p>
              </div>
              <span className="text-xs text-risk-low font-medium bg-risk-low/10 px-2.5 py-1 rounded-full">Enabled</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-sm text-text-primary font-medium">Document Watermarking</p>
                <p className="text-xs text-text-muted">Downloaded documents include user watermark</p>
              </div>
              <span className="text-xs text-text-muted font-medium bg-surface px-2.5 py-1 rounded-full ring-1 ring-canvas-border">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-sm text-text-primary font-medium">Access Expiry</p>
                <p className="text-xs text-text-muted">Auto-revoke access after a set date</p>
              </div>
              <span className="text-xs text-text-muted font-medium bg-surface px-2.5 py-1 rounded-full ring-1 ring-canvas-border">Coming Soon</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
