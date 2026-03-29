import { api } from "./client";
import type { Project } from "../types";

export interface CreateProjectData {
  name: string;
  company_name: string;
  legal_form?: string;
  industry?: string;
  employee_count?: string;
  revenue_size?: string;
  registered_office?: string;
  deal_type?: string;
  description?: string;
}

export interface ProjectMember {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  added_at: string;
}

export const projectsApi = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
  create: (data: CreateProjectData) => api.post<Project>("/projects", data).then((r) => r.data),
  update: (id: string, data: Partial<Project>) => api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),

  // Member management
  listMembers: (projectId: string) =>
    api.get<ProjectMember[]>(`/projects/${projectId}/members`).then((r) => r.data),
  addMember: (projectId: string, email: string) =>
    api.post<ProjectMember>(`/projects/${projectId}/members`, { email }).then((r) => r.data),
  removeMember: (projectId: string, userId: string) =>
    api.delete(`/projects/${projectId}/members/${userId}`),
};
