import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings, UserPlus, Loader2, Users, CheckCircle, XCircle, Clock, Flag } from 'lucide-react';
import { api } from '../../api/client';
import { projectsApi } from '../../api/projects';
import { usePermissions } from '../../hooks/usePermissions';

function DealCompletionSection({ projectId, dealStatus }: { projectId: string; dealStatus?: string }) {
  const queryClient = useQueryClient();
  const { data: status } = useQuery({
    queryKey: ['deal-completion', projectId],
    queryFn: () => projectsApi.getCompletionStatus(projectId),
  });

  const voteMutation = useMutation({
    mutationFn: (vote: "approved" | "rejected") => projectsApi.voteCompletion(projectId, vote),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-completion', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  if (!status) return null;

  return (
    <div className="card p-7 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Flag className="w-6 h-6 text-gold" />
        <h2 className="text-xl font-display font-semibold text-text-primary">Deal Completion</h2>
      </div>

      {dealStatus === 'completed' ? (
        <div className="flex items-center gap-2 p-4 rounded-lg bg-risk-low/10 border border-risk-low/30">
          <CheckCircle size={18} className="text-risk-low" />
          <span className="text-base text-risk-low font-medium">Deal has been completed — all members approved.</span>
        </div>
      ) : (
        <>
          <p className="text-text-secondary text-base">
            All team members must approve before the deal can be marked as completed.
          </p>

          {/* Progress bar */}
          <div className="flex items-center gap-4">
            <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-risk-low rounded-full transition-all duration-300"
                style={{ width: `${status.total_members > 0 ? (status.approved / status.total_members) * 100 : 0}%` }}
              />
            </div>
            <span className="text-sm text-text-secondary shrink-0">
              {status.approved}/{status.total_members} approved
            </span>
          </div>

          {/* Vote buttons */}
          <div className="flex gap-3">
            <button
              className="flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium bg-risk-low/10 text-risk-low hover:bg-risk-low/20 transition-colors"
              onClick={() => voteMutation.mutate("approved")}
              disabled={voteMutation.isPending}
            >
              <CheckCircle size={16} /> Approve Completion
            </button>
            <button
              className="flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium bg-surface text-text-secondary hover:bg-surface-hover transition-colors"
              onClick={() => voteMutation.mutate("rejected")}
              disabled={voteMutation.isPending}
            >
              <XCircle size={16} /> Not Ready
            </button>
          </div>
        </>
      )}

      {/* Member votes */}
      <div className="space-y-2 pt-2">
        {status.votes?.map((v: { user_id: string; name: string; role: string | null; vote: string | null; voted_at: string | null }) => (
          <div key={v.user_id} className="flex items-center justify-between p-3 rounded-lg bg-surface/50 border border-canvas-border">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-surface flex items-center justify-center text-xs font-semibold text-text-secondary">
                {v.name?.charAt(0).toUpperCase()}
              </div>
              <div>
                <span className="text-sm text-text-primary font-medium">{v.name}</span>
                {v.role && <span className="text-xs text-text-muted ml-2 capitalize">{v.role.replace('_', ' ')}</span>}
              </div>
            </div>
            {v.vote === 'approved' ? (
              <span className="flex items-center gap-1 text-xs text-risk-low bg-risk-low/10 rounded-full px-2.5 py-1">
                <CheckCircle size={12} /> Approved
              </span>
            ) : v.vote === 'rejected' ? (
              <span className="flex items-center gap-1 text-xs text-risk-high bg-risk-high/10 rounded-full px-2.5 py-1">
                <XCircle size={12} /> Not Ready
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs text-text-muted">
                <Clock size={12} /> Pending
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

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
        <Settings className="w-8 h-8 text-gold" />
        <div>
          <h1 className="text-3xl font-display font-bold text-text-primary">Deal Settings</h1>
          <p className="text-base text-text-secondary mt-0.5">{project?.name}</p>
        </div>
      </div>

      {/* Deal Info */}
      <div className="card p-7">
        <h2 className="text-xl font-display font-semibold text-text-primary mb-4">Deal Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-base">
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
            <p className="text-text-primary font-medium">{project?.industry || '-'}</p>
          </div>
          <div>
            <span className="text-text-muted">Status</span>
            <p className="text-text-primary font-medium capitalize">{project?.status}</p>
          </div>
          <div>
            <span className="text-text-muted">Created</span>
            <p className="text-text-primary font-medium">{project?.created_at ? new Date(project.created_at).toLocaleDateString() : '-'}</p>
          </div>
        </div>
      </div>

      {/* Add Member */}
      {perms.canManageProject && (
        <div className="card p-7 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-6 h-6 text-gold" />
            <h2 className="text-xl font-display font-semibold text-text-primary">Team Members</h2>
          </div>
          <p className="text-text-secondary text-base">
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
              className="btn-primary px-4 py-2 flex items-center gap-2 text-base"
              disabled={!email.trim() || addMember.isPending}
              onClick={() => addMember.mutate(email.trim())}
            >
              <UserPlus size={16} />
              {addMember.isPending ? 'Adding...' : 'Add Member'}
            </button>
          </div>
          {addError && (
            <p className="text-sm text-risk-high bg-risk-high/10 rounded px-3 py-2">{addError}</p>
          )}
          {addMember.isSuccess && (
            <p className="text-sm text-risk-low bg-risk-low/10 rounded px-3 py-2">Member added successfully.</p>
          )}
        </div>
      )}

      {/* Deal Completion */}
      <DealCompletionSection projectId={projectId!} dealStatus={project?.status} />

      {/* Data Room Controls */}
      {perms.canManageProject && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-text-primary">Data Room Controls</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-base text-text-primary font-medium">NDA Required</p>
                <p className="text-sm text-text-muted">Users must accept NDA before accessing documents</p>
              </div>
              <span className="text-sm text-risk-low font-medium bg-risk-low/10 px-2.5 py-1 rounded-full">Enabled</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-base text-text-primary font-medium">Document Watermarking</p>
                <p className="text-sm text-text-muted">Downloaded documents include user watermark</p>
              </div>
              <span className="text-sm text-text-muted font-medium bg-surface px-2.5 py-1 rounded-full ring-1 ring-canvas-border">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-canvas-border">
              <div>
                <p className="text-base text-text-primary font-medium">Access Expiry</p>
                <p className="text-sm text-text-muted">Auto-revoke access after a set date</p>
              </div>
              <span className="text-sm text-text-muted font-medium bg-surface px-2.5 py-1 rounded-full ring-1 ring-canvas-border">Coming Soon</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
