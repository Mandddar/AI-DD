import { api } from './client';

export interface AuditPlan {
  id: string;
  project_id: string;
  current_phase: string;
  basic_data: Record<string, any> | null;
  risk_analysis: any[] | null;
  dialog_history: any[] | null;
  audit_plan_content: Record<string, any> | null;
  is_approved: boolean;
  created_at: string;
}

export interface RequestItem {
  id: string;
  item_number: number;
  workstream: string;
  audit_field: string;
  question: string;
  answer_document: string | null;
  status: 'open' | 'partial' | 'query' | 'completed';
  priority: 'high' | 'medium' | 'low';
}

export interface BasicDataInput {
  company_name: string;
  legal_form: string;
  registered_office: string;
  industry: string;
  employee_count: number;
  revenue_size: string;
  deal_type: string;
}

export const planning = {
  getPlan: (projectId: string) =>
    api.get<AuditPlan>(`/projects/${projectId}/planning/`).then(r => r.data),

  submitBasicData: (projectId: string, data: BasicDataInput) =>
    api.post<AuditPlan>(`/projects/${projectId}/planning/basic-data`, data).then(r => r.data),

  advancePhase: (projectId: string) =>
    api.post<AuditPlan>(`/projects/${projectId}/planning/advance-phase`).then(r => r.data),

  approvePlan: (projectId: string) =>
    api.post<AuditPlan>(`/projects/${projectId}/planning/approve`).then(r => r.data),

  getRequestList: (projectId: string) =>
    api.get<RequestItem[]>(`/projects/${projectId}/planning/request-list`).then(r => r.data),

  updateRequestItem: (projectId: string, itemId: string, data: Partial<Pick<RequestItem, 'status' | 'priority' | 'answer_document'>>) =>
    api.patch<RequestItem>(`/projects/${projectId}/planning/request-list/${itemId}`, data).then(r => r.data),
};
