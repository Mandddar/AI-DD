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

export const projectsApi = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
  create: (data: CreateProjectData) => api.post<Project>("/projects", data).then((r) => r.data),
  update: (id: string, data: Partial<Project>) => api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
};
