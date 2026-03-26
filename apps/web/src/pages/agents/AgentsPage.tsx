import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Brain, Play, Loader2, CheckCircle, AlertCircle, Clock,
  ChevronRight, FileSearch,
} from "lucide-react";
import { agentsApi, type RunSummary } from "../../api/agents";
import { cn } from "../../lib/utils";

const WORKSTREAM_OPTIONS = [
  { value: "planning", label: "Planning" },
  { value: "legal", label: "Legal" },
  { value: "tax", label: "Tax" },
  { value: "finance", label: "Finance" },
];

function statusIcon(status: RunSummary["status"]) {
  const map = {
    pending: <Clock size={13} className="text-text-muted" />,
    running: <Loader2 size={13} className="animate-spin text-gold" />,
    completed: <CheckCircle size={13} className="text-risk-low" />,
    failed: <AlertCircle size={13} className="text-risk-high" />,
  };
  return map[status];
}

function statusLabel(status: RunSummary["status"]) {
  const map = {
    pending: { label: "Pending", cls: "text-text-muted bg-surface" },
    running: { label: "Running", cls: "text-gold bg-gold/10" },
    completed: { label: "Completed", cls: "text-risk-low bg-risk-low/10" },
    failed: { label: "Failed", cls: "text-risk-high bg-risk-high/10" },
  };
  const { label, cls } = map[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium", cls)}>
      {statusIcon(status)} {label}
    </span>
  );
}

export function AgentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string[]>(["planning", "legal", "tax", "finance"]);

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["agent-runs", projectId],
    queryFn: () => agentsApi.listRuns(projectId!),
    refetchInterval: (query) => {
      const data = query.state.data ?? [];
      return data.some((r) => r.status === "pending" || r.status === "running") ? 2500 : false;
    },
  });

  const triggerMutation = useMutation({
    mutationFn: () => agentsApi.trigger(projectId!, selected),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent-runs", projectId] }),
  });

  const toggle = (ws: string) =>
    setSelected((prev) => prev.includes(ws) ? prev.filter((w) => w !== ws) : [...prev, ws]);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl text-text-primary">AI Analysis</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Run AI agents to analyse uploaded documents and surface due diligence findings.
          </p>
        </div>

        {/* Trigger panel */}
        <div className="card p-4 w-72 space-y-3 shrink-0">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">New Run</p>
          <div className="flex flex-wrap gap-1.5">
            {WORKSTREAM_OPTIONS.map((ws) => (
              <button
                key={ws.value}
                onClick={() => toggle(ws.value)}
                className={cn(
                  "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                  selected.includes(ws.value)
                    ? "bg-gold text-canvas"
                    : "bg-surface text-text-secondary hover:bg-canvas-border"
                )}
              >
                {ws.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending || selected.length === 0}
            className="btn-primary w-full flex items-center justify-center gap-2 text-sm"
          >
            {triggerMutation.isPending
              ? <><Loader2 size={14} className="animate-spin" /> Starting…</>
              : <><Play size={14} /> Run Analysis</>}
          </button>
        </div>
      </div>

      {/* Runs list */}
      {isLoading ? (
        <div className="card p-8 text-center">
          <Loader2 size={24} className="mx-auto animate-spin text-text-muted" />
        </div>
      ) : runs.length === 0 ? (
        <div className="card p-12 text-center">
          <FileSearch size={40} className="mx-auto mb-3 text-text-muted" />
          <p className="text-sm font-medium text-text-secondary">No analysis runs yet</p>
          <p className="mt-1 text-xs text-text-muted">Select workstreams above and click Run Analysis to start.</p>
        </div>
      ) : (
        <div className="card divide-y divide-canvas-border">
          {runs.map((run) => (
            <button
              key={run.id}
              onClick={() => navigate(`/projects/${projectId}/analysis/${run.id}`)}
              className="flex w-full items-center gap-4 px-4 py-3.5 text-left hover:bg-surface/30 transition-colors group"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-gold/10">
                <Brain size={16} className="text-gold" />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-text-primary">
                    Run {new Date(run.created_at).toLocaleDateString("en-GB", {
                      day: "2-digit", month: "short", year: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </p>
                  {statusLabel(run.status)}
                </div>
                <p className="mt-0.5 text-xs text-text-muted">
                  {run.workstreams.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" · ")}
                  {run.status === "running"
                    ? ` · Embedding ${run.processed_documents}/${run.total_documents} docs`
                    : run.finding_count > 0
                    ? ` · ${run.finding_count} finding${run.finding_count !== 1 ? "s" : ""}`
                    : ""}
                </p>
              </div>

              <ChevronRight size={15} className="text-text-muted group-hover:text-text-secondary transition-colors shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
