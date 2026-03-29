import { api } from "./client";

export type Workstream = "legal" | "tax" | "finance" | "general";
export type DocumentStatus = "requested" | "uploaded" | "processing" | "under_review" | "reviewed" | "approved" | "failed";

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
  version_number: number;
  parent_doc_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentText {
  document_id: string;
  content: string;
  extracted_at: string;
}

export interface DocumentTag {
  id: string;
  document_id: string;
  tag: string;
  confidence: number | null;
  source: "ai" | "manual";
  created_at: string;
}

export interface SearchResult {
  id: string;
  name: string;
  original_filename: string;
  workstream: Workstream;
  status: DocumentStatus;
  snippet: string;
  rank: number;
  created_at: string;
}

export const documentsApi = {
  list: (projectId: string, params?: { workstream?: Workstream; status?: DocumentStatus }) =>
    api.get<Document[]>(`/projects/${projectId}/documents`, { params }).then((r) => r.data),

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

  // Search
  search: (projectId: string, query: string) =>
    api.get<SearchResult[]>(`/projects/${projectId}/documents/search`, { params: { q: query } }).then((r) => r.data),

  // Versioning
  uploadVersion: (projectId: string, documentId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Document>(`/projects/${projectId}/documents/${documentId}/versions`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  listVersions: (projectId: string, documentId: string) =>
    api.get<Document[]>(`/projects/${projectId}/documents/${documentId}/versions`).then((r) => r.data),

  // Status
  updateStatus: (projectId: string, documentId: string, status: DocumentStatus) =>
    api.patch<Document>(`/projects/${projectId}/documents/${documentId}/status`, { status }).then((r) => r.data),

  // Tags
  listTags: (projectId: string, documentId: string) =>
    api.get<DocumentTag[]>(`/projects/${projectId}/documents/${documentId}/tags`).then((r) => r.data),

  addTag: (projectId: string, documentId: string, tag: string) =>
    api.post<DocumentTag>(`/projects/${projectId}/documents/${documentId}/tags`, { tag }).then((r) => r.data),

  removeTag: (projectId: string, documentId: string, tagId: string) =>
    api.delete(`/projects/${projectId}/documents/${documentId}/tags/${tagId}`),
};
