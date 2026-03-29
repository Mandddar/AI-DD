import { useState, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, FileText, FileSpreadsheet, File, Trash2,
  CheckCircle, Loader2, AlertCircle, Clock, Download,
  Eye, ShieldCheck, FileSearch, Search, Tag, X, GitBranch,
} from "lucide-react";
import { documentsApi, type Document, type Workstream, type DocumentStatus, type DocumentTag, type SearchResult } from "../../api/documents";
import { cn } from "../../lib/utils";

const WORKSTREAMS: { value: Workstream; label: string }[] = [
  { value: "general", label: "General" },
  { value: "legal", label: "Legal" },
  { value: "tax", label: "Tax" },
  { value: "finance", label: "Finance" },
];

const STATUS_FILTERS: { value: DocumentStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "under_review", label: "Under Review" },
  { value: "reviewed", label: "Reviewed" },
  { value: "approved", label: "Approved" },
  { value: "failed", label: "Failed" },
];

function fileIcon(mimeType: string) {
  if (mimeType.includes("pdf")) return <FileText size={16} className="text-risk-high" />;
  if (mimeType.includes("sheet") || mimeType.includes("excel"))
    return <FileSpreadsheet size={16} className="text-risk-low" />;
  return <File size={16} className="text-text-secondary" />;
}

function statusBadge(status: Document["status"]) {
  const map: Record<Document["status"], { icon: React.ReactNode; label: string; cls: string }> = {
    requested: { icon: <Clock size={11} />, label: "Requested", cls: "text-text-muted bg-surface" },
    uploaded: { icon: <Upload size={11} />, label: "Uploaded", cls: "text-text-secondary bg-surface" },
    processing: { icon: <Loader2 size={11} className="animate-spin" />, label: "Processing", cls: "text-gold bg-gold/10" },
    under_review: { icon: <FileSearch size={11} />, label: "Under Review", cls: "text-gold-light bg-gold/10" },
    reviewed: { icon: <Eye size={11} />, label: "Reviewed", cls: "text-risk-low/80 bg-risk-low/10" },
    approved: { icon: <ShieldCheck size={11} />, label: "Approved", cls: "text-risk-low bg-risk-low/10" },
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

function TagBadges({ projectId, documentId }: { projectId: string; documentId: string }) {
  const { data: tags = [] } = useQuery({
    queryKey: ["tags", documentId],
    queryFn: () => documentsApi.listTags(projectId, documentId),
  });

  if (tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {tags.map((t) => (
        <span
          key={t.id}
          className={cn(
            "inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium",
            t.source === "ai" ? "bg-gold/10 text-gold" : "bg-surface text-text-secondary"
          )}
          title={t.confidence ? `AI confidence: ${Math.round(t.confidence * 100)}%` : "Manual tag"}
        >
          <Tag size={8} /> {t.tag}
        </span>
      ))}
    </div>
  );
}

function StatusActions({ projectId, doc }: { projectId: string; doc: Document }) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (newStatus: DocumentStatus) => documentsApi.updateStatus(projectId, doc.id, newStatus),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", projectId] }),
  });

  const transitions: Partial<Record<DocumentStatus, { label: string; target: DocumentStatus }[]>> = {
    under_review: [{ label: "Mark Reviewed", target: "reviewed" }],
    reviewed: [{ label: "Approve", target: "approved" }, { label: "Back to Review", target: "under_review" }],
    approved: [{ label: "Revert to Reviewed", target: "reviewed" }],
  };

  const actions = transitions[doc.status];
  if (!actions) return null;

  return (
    <div className="flex gap-1">
      {actions.map((a) => (
        <button
          key={a.target}
          onClick={(e) => { e.stopPropagation(); mutation.mutate(a.target); }}
          className="rounded px-2 py-0.5 text-[10px] font-medium bg-gold/10 text-gold hover:bg-gold/20 transition-colors"
          disabled={mutation.isPending}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

function SearchResults({ projectId, query }: { projectId: string; query: string }) {
  const { data: results = [], isLoading } = useQuery({
    queryKey: ["search", projectId, query],
    queryFn: () => documentsApi.search(projectId, query),
    enabled: query.length > 0,
  });

  if (isLoading) return (
    <div className="card p-6 text-center">
      <Loader2 size={18} className="mx-auto animate-spin text-text-muted" />
      <p className="mt-2 text-xs text-text-muted">Searching...</p>
    </div>
  );

  if (results.length === 0) return (
    <div className="card p-6 text-center">
      <Search size={24} className="mx-auto mb-2 text-text-muted" />
      <p className="text-sm text-text-secondary">No results for "{query}"</p>
    </div>
  );

  return (
    <div className="card divide-y divide-canvas-border">
      <div className="px-4 py-2 text-xs text-text-muted">{results.length} result{results.length !== 1 ? "s" : ""}</div>
      {results.map((r) => (
        <div key={r.id} className="px-4 py-3 hover:bg-surface/30 transition-colors">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-text-primary">{r.name}</p>
            {statusBadge(r.status)}
            <span className="text-[10px] text-text-muted capitalize">{r.workstream}</span>
          </div>
          <p
            className="mt-1 text-xs text-text-secondary line-clamp-2"
            dangerouslySetInnerHTML={{ __html: r.snippet.replace(/\*\*/g, '<mark class="bg-gold/20 text-gold rounded px-0.5">').replace(/<mark[^>]*>([^<]*)/g, '<mark class="bg-gold/20 text-gold rounded px-0.5">$1</mark>') }}
          />
        </div>
      ))}
    </div>
  );
}

export function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const qc = useQueryClient();
  const [workstream, setWorkstream] = useState<Workstream>("general");
  const [filterWorkstream, setFilterWorkstream] = useState<Workstream | "all">("all");
  const [filterStatus, setFilterStatus] = useState<DocumentStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState<string[]>([]);

  const listParams: Record<string, string> = {};
  if (filterWorkstream !== "all") listParams.workstream = filterWorkstream;
  if (filterStatus !== "all") listParams.status = filterStatus;

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", projectId, listParams],
    queryFn: () => documentsApi.list(projectId!, listParams as any),
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => d.status === "processing") ? 2000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(projectId!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });

  const handleFiles = async (files: File[]) => {
    for (const file of files) {
      setUploading((prev) => [...prev, file.name]);
      try {
        await documentsApi.upload(projectId!, file, workstream);
        qc.invalidateQueries({ queryKey: ["documents"] });
      } finally {
        setUploading((prev) => prev.filter((n) => n !== file.name));
      }
    }
  };

  const isSearching = searchQuery.trim().length > 0;

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">Documents</h1>
          <p className="mt-1 text-sm text-text-secondary">
            {documents.length} document{documents.length !== 1 ? "s" : ""} ·{" "}
            {documents.filter((d) => !["requested", "processing", "failed"].includes(d.status)).length} reviewed
          </p>
        </div>

        {/* Workstream selector for uploads */}
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
      </div>

      <DropZone onFiles={handleFiles} />

      {/* Search + Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search document content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-full pl-9 pr-8 py-2 text-sm"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary">
              <X size={14} />
            </button>
          )}
        </div>

        <div className="flex rounded border border-canvas-border overflow-hidden">
          {WORKSTREAMS.map((ws) => (
            <button
              key={ws.value}
              onClick={() => setFilterWorkstream(filterWorkstream === ws.value ? "all" : ws.value)}
              className={cn(
                "px-2.5 py-1.5 text-[10px] font-medium transition-colors",
                filterWorkstream === ws.value
                  ? "bg-gold/20 text-gold"
                  : "bg-canvas-card text-text-muted hover:bg-surface"
              )}
            >
              {ws.label}
            </button>
          ))}
        </div>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as DocumentStatus | "all")}
          className="input py-1.5 text-xs"
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      {/* Uploading indicators */}
      {uploading.length > 0 && (
        <div className="space-y-1">
          {uploading.map((name) => (
            <div key={name} className="flex items-center gap-2 rounded bg-gold/5 px-3 py-2 text-xs text-gold">
              <Loader2 size={12} className="animate-spin" />
              Uploading {name}...
            </div>
          ))}
        </div>
      )}

      {/* Search results OR document list */}
      {isSearching ? (
        <SearchResults projectId={projectId!} query={searchQuery.trim()} />
      ) : isLoading ? (
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
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium text-text-primary">{doc.name}</p>
                  {doc.version_number > 1 && (
                    <span className="inline-flex items-center gap-0.5 rounded bg-surface px-1.5 py-0.5 text-[10px] font-medium text-text-secondary" title="Version">
                      <GitBranch size={8} /> v{doc.version_number}
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-muted">
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
                <StatusActions projectId={projectId!} doc={doc} />
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

                <button
                  onClick={() => deleteMutation.mutate(doc.id)}
                  className="text-text-muted hover:text-risk-high transition-colors"
                  title="Delete"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
