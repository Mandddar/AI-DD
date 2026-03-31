import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Loader2, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import { agentsApi, type Finding } from '../../api/agents';
import { usePermissions } from '../../hooks/usePermissions';

export default function RedFlagsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const perms = usePermissions();
  const queryClient = useQueryClient();

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['agent-runs', projectId],
    queryFn: () => agentsApi.listRuns(projectId!),
  });

  const completedRuns = runs.filter(r => r.status === 'completed');
  const latestRun = completedRuns[0];

  const { data: runDetail, isLoading: loadingRun } = useQuery({
    queryKey: ['agent-run', projectId, latestRun?.id],
    queryFn: () => agentsApi.getRun(projectId!, latestRun!.id),
    enabled: !!latestRun,
  });

  const reviewMutation = useMutation({
    mutationFn: ({ findingId, status }: { findingId: string; status: 'approved' | 'rejected' }) =>
      agentsApi.reviewFinding(projectId!, latestRun!.id, findingId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-run', projectId, latestRun?.id] });
    },
  });

  const redFlags: Finding[] = runDetail?.findings.filter(
    f => f.severity === 'critical' || f.severity === 'high'
  ) ?? [];

  if (isLoading || loadingRun) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-7 h-7 text-risk-high" />
          <div>
            <h1 className="text-2xl font-display font-bold text-text-primary">Red Flags</h1>
            <p className="text-sm text-text-secondary mt-0.5">
              Critical and high severity findings requiring immediate attention
            </p>
          </div>
        </div>
        <span className="text-sm text-text-muted">
          {redFlags.length} red flag{redFlags.length !== 1 ? 's' : ''}
        </span>
      </div>

      {!latestRun ? (
        <div className="card p-12 text-center">
          <AlertTriangle className="w-16 h-16 text-text-muted/20 mx-auto mb-4" />
          <h3 className="text-text-primary font-display text-lg mb-2">No Analysis Completed</h3>
          <p className="text-text-secondary text-sm">Run AI analysis first to identify red flags.</p>
          <Link
            to={`/projects/${projectId}/analysis`}
            className="mt-4 inline-flex items-center gap-1.5 text-xs text-gold hover:text-gold-light transition-colors font-medium"
          >
            Go to AI Analysis <ExternalLink size={12} />
          </Link>
        </div>
      ) : redFlags.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle className="w-16 h-16 text-risk-low/30 mx-auto mb-4" />
          <h3 className="text-text-primary font-display text-lg mb-2">No Red Flags</h3>
          <p className="text-text-secondary text-sm">
            No critical or high severity findings in the latest analysis run.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {redFlags.map(finding => (
            <div key={finding.id} className="card p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-text-primary font-medium text-sm">{finding.title}</h3>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${
                      finding.severity === 'critical'
                        ? 'bg-red-500/15 text-red-400 ring-red-500/30'
                        : 'bg-orange-500/15 text-orange-400 ring-orange-500/30'
                    }`}>
                      {finding.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-text-muted px-2 py-0.5 rounded-full bg-surface capitalize">
                      {finding.agent_type}
                    </span>
                    {finding.category && (
                      <span className="text-xs text-text-muted px-2 py-0.5 rounded-full bg-surface">
                        {finding.category}
                      </span>
                    )}
                  </div>

                  <p className="text-text-secondary text-sm mt-2 leading-relaxed">
                    {finding.description}
                  </p>

                  {finding.source_excerpts?.length > 0 && finding.source_excerpts[0] && (
                    <p className="text-text-muted text-xs mt-2 italic border-l-2 border-canvas-border pl-3">
                      {finding.source_excerpts[0]}
                    </p>
                  )}

                  <div className="flex items-center gap-3 mt-3 text-xs text-text-muted">
                    <span>Status: <span className={`font-medium ${
                      finding.status === 'approved' ? 'text-risk-low' :
                      finding.status === 'rejected' ? 'text-risk-high' : 'text-gold'
                    }`}>{finding.status.replace('_', ' ')}</span></span>
                    {finding.reviewed_at && (
                      <span>Reviewed: {new Date(finding.reviewed_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>

                {perms.canReviewFindings && finding.status === 'pending_review' && (
                  <div className="flex gap-1.5 shrink-0">
                    <button
                      className="btn-ghost text-xs px-2.5 py-1.5 flex items-center gap-1 text-risk-low hover:bg-risk-low/10"
                      onClick={() => reviewMutation.mutate({ findingId: finding.id, status: 'approved' })}
                      disabled={reviewMutation.isPending}
                    >
                      <CheckCircle size={13} /> Approve
                    </button>
                    <button
                      className="btn-ghost text-xs px-2.5 py-1.5 flex items-center gap-1 text-risk-high hover:bg-risk-high/10"
                      onClick={() => reviewMutation.mutate({ findingId: finding.id, status: 'rejected' })}
                      disabled={reviewMutation.isPending}
                    >
                      <XCircle size={13} /> Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
