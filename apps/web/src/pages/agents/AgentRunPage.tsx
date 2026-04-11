import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Brain, CheckCircle, XCircle, Clock, Loader2,
  AlertCircle, ChevronDown, ChevronUp, ShieldAlert,
} from "lucide-react";
import { agentsApi, type Finding, type AgentType, type Severity } from "../../api/agents";
import { cn } from "../../lib/utils";
import { usePermissions } from "../../hooks/usePermissions";

const AGENT_LABELS: Record<AgentType, string> = {
  planning: "Planning",
  legal: "Legal",
  tax: "Tax",
  finance: "Finance",
};

const SEVERITY_CONFIG: Record<Severity, { label: string; cls: string; dot: string }> = {
  info: { label: "Info", cls: "text-text-muted bg-surface", dot: "bg-text-muted" },
  low: { label: "Low", cls: "text-risk-low bg-risk-low/10", dot: "bg-risk-low" },
  medium: { label: "Medium", cls: "text-gold bg-gold/10", dot: "bg-gold" },
  high: { label: "High", cls: "text-orange-400 bg-orange-400/10", dot: "bg-orange-400" },
  critical: { label: "Critical", cls: "text-risk-high bg-risk-high/10", dot: "bg-risk-high" },
};

function SeverityBadge({ severity }: { severity: Severity }) {
  const { label, cls } = SEVERITY_CONFIG[severity];
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-sm font-medium", cls)}>
      {label}
    </span>
  );
}

function FindingCard({ finding, projectId, runId, canReview }: { finding: Finding; projectId: string; runId: string; canReview: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const qc = useQueryClient();

  const reviewMutation = useMutation({
    mutationFn: (status: "approved" | "rejected") =>
      agentsApi.reviewFinding(projectId, runId, finding.id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent-run", projectId, runId] }),
  });

  const isPending = finding.status === "pending_review";
  const isApproved = finding.status === "approved";
  const isRejected = finding.status === "rejected";

  return (
    <div className={cn(
      "rounded-lg border transition-colors",
      isApproved ? "border-risk-low/30 bg-risk-low/5" :
      isRejected ? "border-canvas-border bg-canvas-subtle opacity-60" :
      "border-canvas-border bg-canvas-card"
    )}>
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-start gap-3 p-5 text-left"
      >
        <div className={cn("mt-0.5 h-2 w-2 shrink-0 rounded-full", SEVERITY_CONFIG[finding.severity].dot)} />
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-text-muted">{finding.category}</span>
            <SeverityBadge severity={finding.severity} />
            {isApproved && (
              <span className="inline-flex items-center gap-1 text-sm text-risk-low">
                <CheckCircle size={13} /> Approved
              </span>
            )}
            {isRejected && (
              <span className="inline-flex items-center gap-1 text-sm text-text-muted">
                <XCircle size={13} /> Rejected
              </span>
            )}
          </div>
          <p className="text-base font-medium text-text-primary">{finding.title}</p>
        </div>
        {expanded ? (
          <ChevronUp size={16} className="shrink-0 text-text-muted" />
        ) : (
          <ChevronDown size={16} className="shrink-0 text-text-muted" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-canvas-border px-4 pb-4 pt-3 space-y-3">
          <p className="text-base text-text-secondary leading-relaxed">{finding.description}</p>

          {/* Source documents */}
          {finding.source_doc_names?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {finding.source_doc_names.map((name, idx) => (
                <span key={idx} className="inline-flex items-center gap-1.5 rounded-lg bg-highlight/10 text-highlight px-2.5 py-1 text-xs font-medium">
                  <span>{name}</span>
                  {finding.source_pages?.[idx] && (
                    <span className="text-highlight/60">{finding.source_pages[idx]}</span>
                  )}
                </span>
              ))}
            </div>
          )}

          {finding.source_excerpts.length > 0 && (
            <div className="rounded bg-canvas-subtle border border-canvas-border p-3">
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">Source excerpt</p>
              <p className="text-sm text-text-secondary italic line-clamp-4">{finding.source_excerpts[0]}</p>
            </div>
          )}

          {isPending && canReview && (
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => reviewMutation.mutate("approved")}
                disabled={reviewMutation.isPending}
                className="flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium bg-risk-low/10 text-risk-low hover:bg-risk-low/20 transition-colors"
              >
                <CheckCircle size={14} /> Approve
              </button>
              <button
                onClick={() => reviewMutation.mutate("rejected")}
                disabled={reviewMutation.isPending}
                className="flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium bg-surface text-text-secondary hover:bg-canvas-border transition-colors"
              >
                <XCircle size={14} /> Reject
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AgentRunPage() {
  const { projectId, runId } = useParams<{ projectId: string; runId: string }>();
  const navigate = useNavigate();
  const perms = usePermissions();
  const [activeTab, setActiveTab] = useState<AgentType | "all">("all");

  const { data: run, isLoading } = useQuery({
    queryKey: ["agent-run", projectId, runId],
    queryFn: () => agentsApi.getRun(projectId!, runId!),
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "pending" || s === "running" ? 2500 : false;
    },
  });

  if (isLoading || !run) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 size={24} className="animate-spin text-text-muted" />
      </div>
    );
  }

  const tabs: (AgentType | "all")[] = ["all", ...run.workstreams as AgentType[]];
  const visibleFindings = activeTab === "all"
    ? run.findings
    : run.findings.filter((f) => f.agent_type === activeTab);

  const pendingCount = run.findings.filter((f) => f.status === "pending_review").length;
  const approvedCount = run.findings.filter((f) => f.status === "approved").length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Back + header */}
      <div>
        <button
          onClick={() => navigate(`/projects/${projectId}/analysis`)}
          className="mb-3 flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors"
        >
          <ArrowLeft size={15} /> Back to runs
        </button>

        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gold/10">
            <Brain size={20} className="text-gold" />
          </div>
          <div>
            <h1 className="font-display text-2xl text-text-primary">
              Analysis Run
            </h1>
            <p className="text-sm text-text-muted">
              {new Date(run.created_at).toLocaleDateString("en-GB", {
                day: "2-digit", month: "long", year: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </p>
          </div>

          {/* Status */}
          <div className="ml-auto flex items-center gap-2">
            {run.status === "running" && (
              <span className="flex items-center gap-1.5 text-sm text-gold">
                <Loader2 size={15} className="animate-spin" />
                Processing {run.processed_documents}/{run.total_documents} docs
              </span>
            )}
            {run.status === "completed" && (
              <span className="flex items-center gap-1.5 text-sm text-risk-low">
                <CheckCircle size={15} /> Completed
              </span>
            )}
            {run.status === "failed" && (
              <span className="flex items-center gap-1.5 text-sm text-risk-high">
                <AlertCircle size={15} /> Failed
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      {run.status === "completed" && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Total findings", value: run.findings.length, icon: ShieldAlert, cls: "text-text-primary" },
            { label: "Pending review", value: pendingCount, icon: Clock, cls: "text-gold" },
            { label: "Approved", value: approvedCount, icon: CheckCircle, cls: "text-risk-low" },
          ].map(({ label, value, icon: Icon, cls }) => (
            <div key={label} className="card p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm text-text-muted">{label}</p>
                <Icon size={16} className={cls} />
              </div>
              <p className={cn("mt-1 text-2xl font-semibold font-display", cls)}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      {run.findings.length > 0 && (
        <div className="flex gap-1 border-b border-canvas-border">
          {tabs.map((tab) => {
            const count = tab === "all"
              ? run.findings.length
              : run.findings.filter((f) => f.agent_type === tab).length;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-3 py-2 text-base font-medium transition-colors border-b-2 -mb-px",
                  activeTab === tab
                    ? "border-gold text-gold"
                    : "border-transparent text-text-secondary hover:text-text-primary"
                )}
              >
                {tab === "all" ? "All" : AGENT_LABELS[tab as AgentType]}
                <span className="ml-1.5 rounded-full bg-surface px-1.5 py-0.5 text-sm text-text-muted">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Findings */}
      {run.status === "running" || run.status === "pending" ? (
        <div className="card p-10 text-center">
          <Loader2 size={32} className="mx-auto mb-3 animate-spin text-gold" />
          <p className="text-base text-text-secondary">Agents are analysing your documents…</p>
          <p className="mt-1 text-sm text-text-muted">
            {run.processed_documents} of {run.total_documents} documents processed
          </p>
        </div>
      ) : visibleFindings.length === 0 ? (
        <div className="card p-10 text-center">
          <p className="text-base text-text-secondary">No findings for this workstream.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {visibleFindings.map((finding) => (
            <FindingCard
              key={finding.id}
              finding={finding}
              projectId={projectId!}
              runId={runId!}
              canReview={perms.canReviewFindings}
            />
          ))}
        </div>
      )}
    </div>
  );
}
