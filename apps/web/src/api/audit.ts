import { api } from './client';

export interface AuditLog {
  id: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  description: string | null;
  extra_data: Record<string, any> | null;
  ip_address: string | null;
  created_at: string;
}

export const audit = {
  getLogs: (params?: { user_id?: string; action?: string; resource_type?: string; limit?: number; offset?: number }) =>
    api.get<AuditLog[]>('/audit/logs', { params }).then(r => r.data),

  getProjectLogs: (projectId: string, limit: number = 100) =>
    api.get<AuditLog[]>(`/audit/logs/project/${projectId}`, { params: { limit } }).then(r => r.data),
};
