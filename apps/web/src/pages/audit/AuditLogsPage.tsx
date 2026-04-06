import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { audit } from '../../api/audit';
import { Shield, Loader2, Clock, User, Activity, ChevronLeft, ChevronRight } from 'lucide-react';

const PAGE_SIZE = 50;

export default function AuditLogsPage() {
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [page, setPage] = useState(0);

  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs', actionFilter, resourceFilter, page],
    queryFn: () => audit.getLogs({
      action: actionFilter || undefined,
      resource_type: resourceFilter || undefined,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    }),
    refetchInterval: 10000,
  });

  // Reset page when filters change
  const updateAction = (v: string) => { setActionFilter(v); setPage(0); };
  const updateResource = (v: string) => { setResourceFilter(v); setPage(0); };

  if (isLoading && page === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  const hasMore = (logs?.length ?? 0) === PAGE_SIZE;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <Shield className="w-8 h-8 text-gold" />
        <h1 className="text-3xl font-display font-bold text-primary">Audit Trail</h1>
      </div>

      {/* Filters */}
      <div className="card p-5 flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">Action</label>
          <select className="input text-sm" value={actionFilter} onChange={e => updateAction(e.target.value)}>
            <option value="">All Actions</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="document_uploaded">Document Uploaded</option>
            <option value="document_viewed">Document Viewed</option>
            <option value="document_downloaded">Document Downloaded</option>
            <option value="project_created">Project Created</option>
            <option value="agent_run_started">Agent Run Started</option>
            <option value="finding_approved">Finding Approved</option>
            <option value="finding_rejected">Finding Rejected</option>
            <option value="report_generated">Report Generated</option>
            <option value="data_accessed">Data Accessed</option>
          </select>
        </div>
        <div>
          <label className="label">Resource Type</label>
          <select className="input text-sm" value={resourceFilter} onChange={e => updateResource(e.target.value)}>
            <option value="">All Types</option>
            <option value="api">API</option>
            <option value="document">Document</option>
            <option value="project">Project</option>
            <option value="user">User</option>
            <option value="report">Report</option>
          </select>
        </div>

        {/* Pagination controls */}
        <div className="ml-auto flex items-center gap-3">
          <span className="text-secondary text-sm">
            Page {page + 1} {logs ? `(${logs.length} entries)` : ''}
          </span>
          <button
            className="btn-ghost px-2 py-1.5"
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
          >
            <ChevronLeft size={14} />
          </button>
          <button
            className="btn-ghost px-2 py-1.5"
            disabled={!hasMore}
            onClick={() => setPage(p => p + 1)}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Logs */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 size={24} className="mx-auto animate-spin text-text-muted" />
          </div>
        ) : logs?.length ? (
          <div className="divide-y divide-canvas-border/50">
            {logs.map(log => (
              <div key={log.id} className="p-5 hover:bg-surface/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <Activity className="w-5 h-5 text-gold mt-1 flex-shrink-0" />
                    <div>
                      <p className="text-primary text-base">
                        <span className="font-mono text-gold/80">{log.action}</span>
                        {log.resource_type && (
                          <span className="text-secondary ml-2">on {log.resource_type}</span>
                        )}
                      </p>
                      {log.description && (
                        <p className="text-secondary text-sm mt-1">{log.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1.5 text-sm text-text-secondary">
                        {log.user_email && (
                          <span className="flex items-center gap-1">
                            <User className="w-4 h-4" /> {log.user_email}
                          </span>
                        )}
                        {log.ip_address && <span>IP: {log.ip_address}</span>}
                      </div>
                    </div>
                  </div>
                  <span className="text-sm text-text-secondary flex items-center gap-1 flex-shrink-0">
                    <Clock className="w-4 h-4" />
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <Shield className="w-20 h-20 text-secondary/20 mx-auto mb-4" />
            <h3 className="text-primary font-display text-xl mb-2">No Audit Logs</h3>
            <p className="text-secondary text-base">
              {page > 0 ? 'No more entries on this page.' : 'Audit entries will appear here as users interact with the platform.'}
            </p>
          </div>
        )}
      </div>

      <p className="text-sm text-secondary/40 italic">
        Audit logs are tamper-proof - entries can never be edited or deleted, not even by the admin.
      </p>
    </div>
  );
}
