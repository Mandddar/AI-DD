import { api } from "./client";

export type RunStatus = "pending" | "running" | "completed" | "failed";
export type AgentType = "planning" | "legal" | "tax" | "finance";
export type Severity = "info" | "low" | "medium" | "high" | "critical";
export type FindingStatus = "pending_review" | "approved" | "rejected";

export interface Finding {
  id: string;
  run_id: string;
  agent_type: AgentType;
  category: string;
  title: string;
  description: string;
  severity: Severity;
  source_doc_ids: string[];
  source_excerpts: string[];
  status: FindingStatus;
  reviewer_id: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface RunSummary {
  id: string;
  project_id: string;
  triggered_by: string;
  status: RunStatus;
  workstreams: string[];
  total_documents: number;
  processed_documents: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  finding_count: number;
}

export interface Run extends RunSummary {
  findings: Finding[];
}

export const agentsApi = {
  trigger: (projectId: string, workstreams: string[] = ["planning", "legal", "tax", "finance"]) =>
    api.post<RunSummary>(`/projects/${projectId}/agent/runs`, { workstreams }).then((r) => r.data),

  listRuns: (projectId: string) =>
    api.get<RunSummary[]>(`/projects/${projectId}/agent/runs`).then((r) => r.data),

  getRun: (projectId: string, runId: string) =>
    api.get<Run>(`/projects/${projectId}/agent/runs/${runId}`).then((r) => r.data),

  reviewFinding: (projectId: string, runId: string, findingId: string, status: "approved" | "rejected") =>
    api
      .patch<Finding>(`/projects/${projectId}/agent/runs/${runId}/findings/${findingId}`, { status })
      .then((r) => r.data),
};
