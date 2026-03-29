import { api } from './client';

export interface Report {
  id: string;
  project_id: string;
  report_type: 'detailed_workstream' | 'executive_summary' | 'consolidated';
  report_format: string;
  workstream: string | null;
  title: string;
  content: Record<string, any>;
  edited_content: Record<string, any> | null;
  is_finalized: boolean;
  storage_path: string | null;
  created_at: string;
}

export interface ReportCreate {
  report_type: string;
  workstream?: string;
  title: string;
}

export const reports = {
  list: (projectId: string) =>
    api.get<Report[]>(`/projects/${projectId}/reports/`).then(r => r.data),

  get: (projectId: string, reportId: string) =>
    api.get<Report>(`/projects/${projectId}/reports/${reportId}`).then(r => r.data),

  generate: (projectId: string, data: ReportCreate) =>
    api.post<Report>(`/projects/${projectId}/reports/generate`, data).then(r => r.data),

  editContent: (projectId: string, reportId: string, editedContent: Record<string, any>) =>
    api.patch<Report>(`/projects/${projectId}/reports/${reportId}/edit`, { edited_content: editedContent }).then(r => r.data),

  finalize: (projectId: string, reportId: string) =>
    api.post<Report>(`/projects/${projectId}/reports/${reportId}/finalize`).then(r => r.data),
};
