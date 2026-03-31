import { useState, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, FileText, FileSpreadsheet, File, Trash2,
  CheckCircle, Loader2, AlertCircle, Clock, Download,
} from "lucide-react";
import { documentsApi, type Document, type Workstream } from "../../api/documents";
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

function statusBadge(status: Document["status"]) {
  const map = {
    uploaded: { icon: <Clock size={11} />, label: "Uploaded", cls: "text-text-muted bg-surface" },
    processing: { icon: <Loader2 size={11} className="animate-spin" />, label: "Processing", cls: "text-gold bg-gold/10" },
    ready: { icon: <CheckCircle size={11} />, label: "Ready", cls: "text-risk-low bg-risk-low/10" },
    failed: { icon: <AlertCircle size={11} />, label: "Failed", cls: "text-risk-high bg-risk-high/10" },
  };
  const { icon, label, cls } = map[status];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", cls)}>
      {icon} {label}
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
      <Upload size={28} className={cn("mb-3", dragging ? "text-gold" : "text-text-muted")} />
      <p className="text-sm font-medium text-text-primary">Drop files here or click to browse</p>
      <p className="mt-1 text-xs text-text-muted">PDF, Word, Excel, CSV — up to 50 MB</p>
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
    <div className="p-6 animate-fade-in">
      <div className="card max-w-2xl mx-auto p-8 space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold/10 ring-1 ring-gold/30">
            <FileText size={24} className="text-gold" />
          </div>
          <h2 className="font-display text-xl text-text-primary">Non-Disclosure Agreement</h2>
          <p className="mt-2 text-sm text-text-secondary">
            Before accessing documents for this deal, you must accept the NDA terms.
          </p>
        </div>
        <div className="bg-surface rounded-lg border border-canvas-border p-4 text-sm text-text-secondary space-y-3 max-h-64 overflow-y-auto">
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

export function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const qc = useQueryClient();
  const perms = usePermissions();
  const [workstream, setWorkstream] = useState<Workstream>("general");
  const [uploading, setUploading] = useState<string[]>([]);

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentsApi.list(projectId!),
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => d.status === "processing" || d.status === "uploaded") ? 2000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(projectId!, id),
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

  return (
    <NdaGate projectId={projectId!}>
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">Documents</h1>
          <p className="mt-1 text-sm text-text-secondary">
            {documents.length} document{documents.length !== 1 ? "s" : ""} ·{" "}
            {documents.filter((d) => d.status === "ready").length} ready
          </p>
        </div>

        {/* Workstream selector */}
        {perms.canUploadDocuments && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Upload to:</span>
            <div className="flex rounded border border-canvas-border overflow-hidden">
              {WORKSTREAMS.map((ws) => (
                <button
                  key={ws.value}
                  onClick={() => setWorkstream(ws.value)}
                  className={cn(
                    "px-3 py-1.5 text-xs font-medium transition-colors",
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

      {perms.isReadOnly && (
        <div className="rounded-lg border border-canvas-border bg-surface/50 px-4 py-2.5 text-sm text-text-secondary">
          Read-only access — you can view and download approved documents.
        </div>
      )}

      {perms.canUploadDocuments && <DropZone onFiles={handleFiles} />}

      {/* Uploading indicators */}
      {uploading.length > 0 && (
        <div className="space-y-1">
          {uploading.map((name) => (
            <div key={name} className="flex items-center gap-2 rounded bg-gold/5 px-3 py-2 text-xs text-gold">
              <Loader2 size={12} className="animate-spin" />
              Uploading {name}…
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
          <p className="text-sm text-text-secondary">No documents yet. Drop files above to get started.</p>
        </div>
      ) : (
        <div className="card divide-y divide-canvas-border">
          {documents.map((doc) => (
            <div key={doc.id} className="flex items-center gap-4 px-4 py-3 hover:bg-surface/30 transition-colors">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-surface">
                {fileIcon(doc.mime_type)}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-text-primary">{doc.name}</p>
                <p className="text-xs text-text-muted">
                  {formatBytes(doc.size_bytes)}
                  {doc.page_count ? ` · ${doc.page_count} pages` : ""}
                  {" · "}
                  <span className="capitalize">{doc.workstream}</span>
                  {" · "}
                  {new Date(doc.created_at).toLocaleDateString("en-GB")}
                </p>
              </div>

              <div className="flex items-center gap-3">
                {statusBadge(doc.status)}

                <a
                  href={documentsApi.downloadUrl(doc.project_id, doc.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-text-muted hover:text-text-secondary transition-colors"
                  title="Download"
                >
                  <Download size={14} />
                </a>

                {perms.canDeleteDocuments && (
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    className="text-text-muted hover:text-risk-high transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
    </NdaGate>
  );
}
