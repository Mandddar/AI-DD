import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { audit } from '../../api/audit';
import { Shield, Search, Loader2, Clock, User, Activity } from 'lucide-react';

export default function AuditLogsPage() {
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');

  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs', actionFilter, resourceFilter],
    queryFn: () => audit.getLogs({
      action: actionFilter || undefined,
      resource_type: resourceFilter || undefined,
      limit: 200,
    }),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Shield className="w-7 h-7 text-gold" />
        <h1 className="text-2xl font-display font-bold text-primary">Audit Trail</h1>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">Action</label>
          <select className="input text-sm" value={actionFilter} onChange={e => setActionFilter(e.target.value)}>
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
          <select className="input text-sm" value={resourceFilter} onChange={e => setResourceFilter(e.target.value)}>
            <option value="">All Types</option>
            <option value="api">API</option>
            <option value="document">Document</option>
            <option value="project">Project</option>
            <option value="user">User</option>
            <option value="report">Report</option>
          </select>
        </div>
        <span className="text-secondary text-xs ml-auto">{logs?.length || 0} entries</span>
      </div>

      {/* Logs */}
      <div className="card overflow-hidden">
        {logs?.length ? (
          <div className="divide-y divide-canvas-border/50">
            {logs.map(log => (
              <div key={log.id} className="p-4 hover:bg-surface/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <Activity className="w-4 h-4 text-gold mt-1 flex-shrink-0" />
                    <div>
                      <p className="text-primary text-sm">
                        <span className="font-mono text-gold/80">{log.action}</span>
                        {log.resource_type && (
                          <span className="text-secondary ml-2">on {log.resource_type}</span>
                        )}
                      </p>
                      {log.description && (
                        <p className="text-secondary text-xs mt-1">{log.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-secondary/60">
                        {log.user_email && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" /> {log.user_email}
                          </span>
                        )}
                        {log.ip_address && <span>IP: {log.ip_address}</span>}
                      </div>
                    </div>
                  </div>
                  <span className="text-xs text-secondary/60 flex items-center gap-1 flex-shrink-0">
                    <Clock className="w-3 h-3" />
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <Shield className="w-16 h-16 text-secondary/20 mx-auto mb-4" />
            <h3 className="text-primary font-display text-lg mb-2">No Audit Logs</h3>
            <p className="text-secondary text-sm">Audit entries will appear here as users interact with the platform.</p>
          </div>
        )}
      </div>

      <p className="text-xs text-secondary/40 italic">
        Audit logs are tamper-proof — entries can never be edited or deleted, not even by the admin.
      </p>
    </div>
  );
}
