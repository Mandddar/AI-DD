import { useState, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, FileText, FileSpreadsheet, File, Trash2,
  CheckCircle, Loader2, AlertCircle, Clock, Download,
  Search, Tag, GitBranch, ChevronDown, ChevronUp,
  Eye, ShieldCheck, XCircle, Archive,
  FolderOpen, FolderPlus, ChevronRight, CheckSquare, Square,
} from "lucide-react";
import { documentsApi, type Document, type DocumentTag, type SearchResult, type Workstream, type DocumentStatus, type Folder } from "../../api/documents";
import { cn } from "../../lib/utils";
import { usePermissions } from "../../hooks/usePermissions";

const WORKSTREAMS: { value: Workstream; label: string }[] = [
  { value: "general", label: "General" },
  { value: "legal", label: "Legal" },
  { value: "tax", label: "Tax" },
  { value: "finance", label: "Finance" },
];

function fileIcon(mimeType: string) {
  if (mimeType.includes("pdf")) return <FileText size={16} className="text-risk-high" />;
  if (mimeType.includes("sheet") || mimeType.includes("excel"))
    return <FileSpreadsheet size={16} className="text-risk-low" />;
  return <File size={16} className="text-text-secondary" />;
}

// 7-state lifecycle status badges (spec §6.1)
function statusBadge(status: DocumentStatus) {
  const map: Record<DocumentStatus, { icon: React.ReactNode; label: string; cls: string }> = {
    requested: { icon: <Clock size={11} />, label: "Requested", cls: "text-text-muted bg-surface" },
    uploaded: { icon: <Clock size={11} />, label: "Uploaded", cls: "text-text-muted bg-surface" },
    processing: { icon: <Loader2 size={11} className="animate-spin" />, label: "Processing", cls: "text-gold bg-gold/10" },
    ready: { icon: <CheckCircle size={11} />, label: "Ready", cls: "text-risk-low bg-risk-low/10" },
    under_review: { icon: <Eye size={11} />, label: "Under Review", cls: "text-gold bg-gold/10" },
    reviewed: { icon: <ShieldCheck size={11} />, label: "Reviewed", cls: "text-blue-400 bg-blue-400/10" },
    approved: { icon: <CheckCircle size={11} />, label: "Approved", cls: "text-risk-low bg-risk-low/10" },
    rejected: { icon: <XCircle size={11} />, label: "Rejected", cls: "text-risk-high bg-risk-high/10" },
    archived: { icon: <Archive size={11} />, label: "Archived", cls: "text-text-muted bg-surface" },
    failed: { icon: <AlertCircle size={11} />, label: "Failed", cls: "text-risk-high bg-risk-high/10" },
  };
  const entry = map[status] || map.uploaded;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-sm font-medium", entry.cls)}>
      {entry.icon} {entry.label}
    </span>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function DropZone({ onFiles }: { onFiles: (files: File[]) => void }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length) onFiles(files);
  }, [onFiles]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 transition-colors",
        dragging
          ? "border-gold bg-gold/5"
          : "border-canvas-border bg-canvas-subtle hover:border-gold/50 hover:bg-gold/5"
      )}
    >
      <Upload size={32} className={cn("mb-3", dragging ? "text-gold" : "text-text-muted")} />
      <p className="text-base font-medium text-text-primary">Drop files here or click to browse</p>
      <p className="mt-1 text-sm text-text-muted">PDF, Word, Excel, CSV - up to 50 MB</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt"
        className="hidden"
        onChange={(e) => { if (e.target.files) onFiles(Array.from(e.target.files)); }}
      />
    </div>
  );
}

function NdaGate({ projectId, children }: { projectId: string; children: React.ReactNode }) {
  const ndaKey = `nda_accepted_${projectId}`;
  const [accepted, setAccepted] = useState(() => sessionStorage.getItem(ndaKey) === "true");

  if (accepted) return <>{children}</>;

  return (
    <div className="p-7 animate-fade-in">
      <div className="card max-w-2xl mx-auto p-8 space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold/10 ring-1 ring-gold/30">
            <FileText size={24} className="text-gold" />
          </div>
          <h2 className="font-display text-2xl text-text-primary">Non-Disclosure Agreement</h2>
          <p className="mt-2 text-base text-text-secondary">
            Before accessing documents for this deal, you must accept the NDA terms.
          </p>
        </div>
        <div className="bg-surface rounded-lg border border-canvas-border p-4 text-base text-text-secondary space-y-3 max-h-64 overflow-y-auto">
          <p>
            By accessing the data room for this deal, you acknowledge and agree that all information,
            documents, and materials contained herein are strictly confidential and proprietary.
          </p>
          <p>
            You agree not to disclose, copy, distribute, or use any information obtained through this
            data room for any purpose other than the evaluation of the proposed transaction.
          </p>
          <p>
            Unauthorized disclosure may result in legal action. This obligation survives the termination
            of your access to the data room.
          </p>
          <p>
            All AI-generated analyses of these documents are subject to the same confidentiality obligations.
          </p>
        </div>
        <div className="flex justify-center gap-3">
          <a href="/projects" className="btn-ghost px-6 py-2">Decline</a>
          <button
            className="btn-primary px-6 py-2"
            onClick={() => { sessionStorage.setItem(ndaKey, "true"); setAccepted(true); }}
          >
            I Accept the NDA Terms
          </button>
        </div>
      </div>
    </div>
  );
}

function TagBadges({ projectId, documentId }: { projectId: string; documentId: string }) {
  const { data: tags = [] } = useQuery({
    queryKey: ["doc-tags", projectId, documentId],
    queryFn: () => documentsApi.getTags(projectId, documentId),
    staleTime: 60_000,
  });

  if (tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {tags.slice(0, 4).map((t) => (
        <span
          key={t.id}
          className={cn(
            "inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-medium",
            t.source === "ai" ? "bg-gold/10 text-gold" : "bg-surface text-text-secondary"
          )}
          title={t.confidence ? `Confidence: ${Math.round(t.confidence * 100)}%` : "Manual tag"}
        >
          <Tag size={8} />
          {t.tag}
        </span>
      ))}
      {tags.length > 4 && (
        <span className="text-xs text-text-muted">+{tags.length - 4}</span>
      )}
    </div>
  );
}

export function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const qc = useQueryClient();
  const perms = usePermissions();
  const [workstream, setWorkstream] = useState<Workstream>("general");
  const [uploading, setUploading] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [folderPath, setFolderPath] = useState<{ id?: string; name: string }[]>([{ name: "Root" }]);
  const [newFolderName, setNewFolderName] = useState("");
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentsApi.list(projectId!),
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => d.status === "processing" || d.status === "uploaded") ? 2000 : false;
    },
  });

  const { data: searchResults = [], isFetching: searching } = useQuery({
    queryKey: ["doc-search", projectId, searchQuery],
    queryFn: () => documentsApi.search(projectId!, searchQuery),
    enabled: searchQuery.length >= 2,
    staleTime: 10_000,
  });

  const { data: folders = [] } = useQuery({
    queryKey: ["folders", projectId, currentFolderId],
    queryFn: () => documentsApi.listFolders(projectId!, currentFolderId),
  });

  const createFolderMutation = useMutation({
    mutationFn: (name: string) => documentsApi.createFolder(projectId!, name, currentFolderId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["folders", projectId] }); setNewFolderName(""); },
  });

  const initFoldersMutation = useMutation({
    mutationFn: () => documentsApi.initFolders(projectId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["folders", projectId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(projectId!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: () => documentsApi.bulkDelete(projectId!, Array.from(selectedDocs)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["documents", projectId] }); setSelectedDocs(new Set()); },
  });

  const bulkStatusMutation = useMutation({
    mutationFn: (status: DocumentStatus) => documentsApi.bulkUpdateStatus(projectId!, Array.from(selectedDocs), status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["documents", projectId] }); setSelectedDocs(new Set()); },
  });

  const statusMutation = useMutation({
    mutationFn: ({ docId, status }: { docId: string; status: DocumentStatus }) =>
      documentsApi.updateStatus(projectId!, docId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });

  const handleFiles = async (files: File[]) => {
    for (const file of files) {
      setUploading((prev) => [...prev, file.name]);
      try {
        await documentsApi.upload(projectId!, file, workstream);
        qc.invalidateQueries({ queryKey: ["documents", projectId] });
      } finally {
        setUploading((prev) => prev.filter((n) => n !== file.name));
      }
    }
  };

  const toggleSelect = (docId: string) => {
    setSelectedDocs((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedDocs.size === documents.length) setSelectedDocs(new Set());
    else setSelectedDocs(new Set(documents.map((d) => d.id)));
  };

  const navigateToFolder = (folderId: string, folderName: string) => {
    setCurrentFolderId(folderId);
    setFolderPath((prev) => [...prev, { id: folderId, name: folderName }]);
    setSelectedDocs(new Set());
  };

  const navigateUp = (index: number) => {
    const entry = folderPath[index];
    setCurrentFolderId(entry.id);
    setFolderPath((prev) => prev.slice(0, index + 1));
    setSelectedDocs(new Set());
  };

  // Determine available next statuses for a document
  const getNextStatuses = (status: DocumentStatus): DocumentStatus[] => {
    const transitions: Record<string, DocumentStatus[]> = {
      ready: ["under_review"],
      under_review: ["reviewed", "rejected"],
      reviewed: ["approved", "rejected"],
      rejected: ["under_review"],
    };
    return transitions[status] || [];
  };

  return (
    <NdaGate projectId={projectId!}>
    <div className="p-7 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">Documents</h1>
          <p className="mt-1 text-base text-text-secondary">
            {documents.length} document{documents.length !== 1 ? "s" : ""} ·{" "}
            {documents.filter((d) => d.status === "ready" || d.status === "approved").length} ready
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Full-text search toggle */}
          <button
            onClick={() => setShowSearch(!showSearch)}
            className={cn(
              "flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors",
              showSearch ? "bg-gold text-canvas" : "bg-surface text-text-secondary hover:bg-surface-hover"
            )}
          >
            <Search size={14} /> Search
          </button>

          {/* Workstream selector */}
          {perms.canUploadDocuments && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-muted">Upload to:</span>
              <div className="flex rounded border border-canvas-border overflow-hidden">
                {WORKSTREAMS.map((ws) => (
                  <button
                    key={ws.value}
                    onClick={() => setWorkstream(ws.value)}
                    className={cn(
                      "px-3 py-1.5 text-sm font-medium transition-colors",
                      workstream === ws.value
                        ? "bg-gold text-canvas"
                        : "bg-canvas-card text-text-secondary hover:bg-surface"
                    )}
                  >
                    {ws.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Full-text search */}
      {showSearch && (
        <div className="card p-4 space-y-3 animate-fade-in">
          <div className="flex items-center gap-2">
            <Search size={16} className="text-text-muted" />
            <input
              className="input flex-1"
              placeholder="Search document contents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            {searching && <Loader2 size={16} className="animate-spin text-gold" />}
          </div>
          {searchResults.length > 0 && (
            <div className="divide-y divide-canvas-border max-h-64 overflow-y-auto">
              {searchResults.map((r, i) => (
                <div key={i} className="py-2 px-1">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-medium text-text-primary">{r.document_name}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-surface text-text-muted capitalize">{r.workstream}</span>
                  </div>
                  <p className="text-sm text-text-secondary mt-0.5 line-clamp-2">{r.snippet}</p>
                </div>
              ))}
            </div>
          )}
          {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
            <p className="text-sm text-text-muted text-center py-2">No results found.</p>
          )}
        </div>
      )}

      {/* Folder Navigation */}
      <div className="card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-base">
            {folderPath.map((entry, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight size={12} className="text-text-muted" />}
                <button onClick={() => navigateUp(i)}
                  className={cn("hover:text-gold transition-colors", i === folderPath.length - 1 ? "text-text-primary font-medium" : "text-text-secondary")}>
                  {entry.name}
                </button>
              </span>
            ))}
          </div>
          {perms.canDeleteDocuments && (
            <div className="flex items-center gap-2">
              {folders.length === 0 && !currentFolderId && (
                <button onClick={() => initFoldersMutation.mutate()}
                  className="btn-ghost text-sm px-3 py-1.5 flex items-center gap-1" disabled={initFoldersMutation.isPending}>
                  <FolderPlus size={12} /> Init Default Folders
                </button>
              )}
              <div className="flex items-center gap-1">
                <input className="input text-sm py-1 px-2 w-32" placeholder="New folder..." value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && newFolderName.trim()) createFolderMutation.mutate(newFolderName.trim()); }}
                />
                <button onClick={() => newFolderName.trim() && createFolderMutation.mutate(newFolderName.trim())}
                  className="btn-ghost text-sm px-2 py-1" disabled={!newFolderName.trim()}>
                  <FolderPlus size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
        {folders.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {folders.map((f) => (
              <button key={f.id} onClick={() => navigateToFolder(f.id, f.name)}
                className="flex items-center gap-1.5 rounded-lg border border-canvas-border bg-surface px-3 py-2 text-base text-text-primary hover:bg-surface-hover transition-colors">
                <FolderOpen size={14} className="text-gold" /> {f.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bulk Operations Toolbar */}
      {selectedDocs.size > 0 && perms.canDeleteDocuments && (
        <div className="card px-4 py-3 flex items-center gap-4 bg-gold/5 border-gold/30">
          <span className="text-base text-gold font-medium">{selectedDocs.size} selected</span>
          <button onClick={() => bulkStatusMutation.mutate("under_review")}
            className="btn-ghost text-sm px-3 py-1.5">Mark Under Review</button>
          <button onClick={() => bulkStatusMutation.mutate("approved")}
            className="btn-ghost text-sm px-3 py-1.5">Approve</button>
          <button onClick={() => { if (confirm(`Delete ${selectedDocs.size} documents?`)) bulkDeleteMutation.mutate(); }}
            className="btn-ghost text-sm px-3 py-1.5 text-risk-high">Delete Selected</button>
          <button onClick={() => setSelectedDocs(new Set())}
            className="btn-ghost text-sm px-3 py-1.5 ml-auto">Clear Selection</button>
        </div>
      )}

      {perms.isReadOnly && (
        <div className="rounded-lg border border-canvas-border bg-surface/50 px-4 py-2.5 text-base text-text-secondary">
          Read-only access - you can view and download approved documents.
        </div>
      )}

      {perms.canUploadDocuments && <DropZone onFiles={handleFiles} />}

      {/* Uploading indicators */}
      {uploading.length > 0 && (
        <div className="space-y-1">
          {uploading.map((name) => (
            <div key={name} className="flex items-center gap-2 rounded bg-gold/5 px-3 py-2 text-sm text-gold">
              <Loader2 size={12} className="animate-spin" />
              Uploading {name}...
            </div>
          ))}
        </div>
      )}

      {/* Document list */}
      {isLoading ? (
        <div className="card p-8 text-center">
          <Loader2 size={24} className="mx-auto animate-spin text-text-muted" />
        </div>
      ) : documents.length === 0 ? (
        <div className="card p-10 text-center">
          <FileText size={36} className="mx-auto mb-3 text-text-muted" />
          <p className="text-base text-text-secondary">No documents yet. Drop files above to get started.</p>
        </div>
      ) : (
        <div className="card divide-y divide-canvas-border">
          {documents.map((doc) => {
            const nextStatuses = perms.canDeleteDocuments ? getNextStatuses(doc.status) : [];

            return (
              <div key={doc.id} className="flex items-center gap-4 px-4 py-3 hover:bg-surface/30 transition-colors">
                {perms.canDeleteDocuments && (
                  <button onClick={() => toggleSelect(doc.id)} className="text-text-muted hover:text-gold shrink-0">
                    {selectedDocs.has(doc.id) ? <CheckSquare size={16} className="text-gold" /> : <Square size={16} />}
                  </button>
                )}
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-surface">
                  {fileIcon(doc.mime_type)}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-base font-medium text-text-primary">{doc.name}</p>
                    {doc.version_number > 1 && (
                      <span className="inline-flex items-center gap-0.5 text-xs text-text-muted bg-surface rounded px-1.5 py-0.5">
                        <GitBranch size={8} /> v{doc.version_number}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-text-muted">
                    {formatBytes(doc.size_bytes)}
                    {doc.page_count ? ` · ${doc.page_count} pages` : ""}
                    {" · "}
                    <span className="capitalize">{doc.workstream}</span>
                    {" · "}
                    {new Date(doc.created_at).toLocaleDateString("en-GB")}
                  </p>
                  <TagBadges projectId={projectId!} documentId={doc.id} />
                </div>

                <div className="flex items-center gap-3">
                  {statusBadge(doc.status)}

                  {/* Status transition buttons */}
                  {nextStatuses.length > 0 && (
                    <div className="flex gap-1">
                      {nextStatuses.map((ns) => (
                        <button
                          key={ns}
                          onClick={() => statusMutation.mutate({ docId: doc.id, status: ns })}
                          className="text-xs px-1.5 py-0.5 rounded bg-surface hover:bg-surface-hover text-text-secondary transition-colors capitalize"
                          title={`Move to ${ns.replace('_', ' ')}`}
                        >
                          {ns.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={() => setPreviewDoc(doc)}
                    className="text-text-muted hover:text-gold transition-colors"
                    title="Preview"
                  >
                    <Eye size={16} />
                  </button>

                  <a
                    href={documentsApi.downloadUrl(doc.project_id, doc.id)}
                    className="text-text-muted hover:text-text-secondary transition-colors"
                    title="Download"
                  >
                    <Download size={16} />
                  </a>

                  {perms.canDeleteDocuments && (
                    <button
                      onClick={() => deleteMutation.mutate(doc.id)}
                      className="text-text-muted hover:text-risk-high transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>

    {/* Document Preview Modal */}
    {previewDoc && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setPreviewDoc(null)}>
        <div className="relative bg-canvas rounded-xl border border-canvas-border shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between px-5 py-3 border-b border-canvas-border">
            <div className="flex items-center gap-3 min-w-0">
              {fileIcon(previewDoc.mime_type)}
              <span className="text-base font-medium text-text-primary truncate">{previewDoc.name}</span>
              {statusBadge(previewDoc.status)}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <a
                href={documentsApi.downloadUrl(previewDoc.project_id, previewDoc.id)}
                className="btn-ghost px-3 py-1.5 text-sm flex items-center gap-1.5"
                title="Download"
              >
                <Download size={14} /> Download
              </a>
              <button onClick={() => setPreviewDoc(null)} className="btn-ghost px-2 py-1.5" title="Close">
                <XCircle size={16} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            {previewDoc.mime_type.includes("pdf") ? (
              <iframe
                src={documentsApi.previewUrl(previewDoc.project_id, previewDoc.id)}
                className="w-full h-full border-0"
                title={previewDoc.name}
              />
            ) : previewDoc.mime_type.startsWith("image/") ? (
              <div className="flex items-center justify-center h-full p-4">
                <img
                  src={documentsApi.previewUrl(previewDoc.project_id, previewDoc.id)}
                  alt={previewDoc.name}
                  className="max-w-full max-h-full object-contain"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full gap-4 text-text-secondary">
                <FileText size={48} className="text-text-muted" />
                <p className="text-base">Preview not available for this file type.</p>
                <a
                  href={documentsApi.downloadUrl(previewDoc.project_id, previewDoc.id)}
                  className="btn-primary px-4 py-2 text-base flex items-center gap-2"
                >
                  <Download size={14} /> Download File
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    )}
    </NdaGate>
  );
}
