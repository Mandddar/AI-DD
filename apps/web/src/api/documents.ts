import { api } from "./client";

export type Workstream = "legal" | "tax" | "finance" | "general";
export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  project_id: string;
  uploaded_by: string;
  name: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  workstream: Workstream;
  status: DocumentStatus;
  page_count: string | null;
  created_at: string;
}

export interface DocumentText {
  document_id: string;
  content: string;
  extracted_at: string;
}

export const documentsApi = {
  list: (projectId: string) =>
    api.get<Document[]>(`/projects/${projectId}/documents`).then((r) => r.data),

  upload: (projectId: string, file: File, workstream: Workstream = "general") => {
    const form = new FormData();
    form.append("file", file);
    form.append("workstream", workstream);
    return api.post<Document>(`/projects/${projectId}/documents`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  getText: (projectId: string, documentId: string) =>
    api.get<DocumentText>(`/projects/${projectId}/documents/${documentId}/text`).then((r) => r.data),

  delete: (projectId: string, documentId: string) =>
    api.delete(`/projects/${projectId}/documents/${documentId}`),

  downloadUrl: (projectId: string, documentId: string) =>
    `${api.defaults.baseURL}/projects/${projectId}/documents/${documentId}/download`,
};
