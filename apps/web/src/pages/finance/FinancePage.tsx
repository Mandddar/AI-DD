import { useState, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, Loader2, CheckCircle, AlertCircle, Clock, Trash2,
  TrendingUp, TrendingDown, Minus, BarChart3, HelpCircle,
  FileSpreadsheet, Play, ThumbsUp, ThumbsDown,
} from "lucide-react";
import { financeApi, type Dataset, type VarianceResult, type FinanceQuery as FQuery } from "../../api/finance";
import { cn } from "../../lib/utils";

const SIGNIFICANCE_STYLES = {
  normal: "text-text-muted bg-surface",
  notable: "text-gold bg-gold/10",
  significant: "text-risk-medium bg-risk-medium/10",
  critical: "text-risk-high bg-risk-high/10",
};

function significanceBadge(sig: string) {
  const cls = SIGNIFICANCE_STYLES[sig as keyof typeof SIGNIFICANCE_STYLES] || SIGNIFICANCE_STYLES.normal;
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase", cls)}>
      {sig}
    </span>
  );
}

function formatEur(value: number | null) {
  if (value === null) return "—";
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

function formatPct(value: number | null) {
  if (value === null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function formatPeriod(p: string) {
  const d = new Date(p);
  return d.toLocaleDateString("en-GB", { month: "short", year: "numeric" });
}

// --- Upload Tab ---

function OverviewTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const { data: datasets = [], isLoading: loadingDs } = useQuery({
    queryKey: ["finance-datasets", projectId],
    queryFn: () => financeApi.listDatasets(projectId),
    refetchInterval: (q) => (q.state.data ?? []).some((d) => d.status === "processing") ? 2000 : false,
  });

  const { data: summary } = useQuery({
    queryKey: ["finance-summary", projectId],
    queryFn: () => financeApi.getSummary(projectId),
    enabled: datasets.some((d) => d.status === "completed"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => financeApi.deleteDataset(projectId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance-datasets"] }),
  });

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await financeApi.importData(projectId, file);
      qc.invalidateQueries({ queryKey: ["finance-datasets"] });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload area */}
      <div
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-canvas-border bg-canvas-subtle p-8 hover:border-gold/50 hover:bg-gold/5 transition-colors"
      >
        <FileSpreadsheet size={28} className="mb-3 text-text-muted" />
        <p className="text-sm font-medium text-text-primary">Upload financial data</p>
        <p className="mt-1 text-xs text-text-muted">Excel (.xlsx) or TSV — German or English format</p>
        <input ref={inputRef} type="file" className="hidden" accept=".xlsx,.xls,.tsv,.txt"
          onChange={(e) => { if (e.target.files?.[0]) handleUpload(e.target.files[0]); }} />
      </div>

      {uploading && (
        <div className="flex items-center gap-2 rounded bg-gold/5 px-3 py-2 text-xs text-gold">
          <Loader2 size={12} className="animate-spin" /> Importing...
        </div>
      )}

      {/* Dataset list */}
      {loadingDs ? (
        <div className="card p-6 text-center"><Loader2 size={18} className="mx-auto animate-spin text-text-muted" /></div>
      ) : datasets.length > 0 && (
        <div className="card divide-y divide-canvas-border">
          <div className="px-4 py-2 text-xs text-text-muted font-medium">Imported Datasets</div>
          {datasets.map((ds) => (
            <div key={ds.id} className="flex items-center gap-4 px-4 py-3">
              <FileSpreadsheet size={16} className="text-risk-low shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary truncate">{ds.source_filename}</p>
                <p className="text-xs text-text-muted">
                  {ds.chart_of_accounts.toUpperCase()} · {ds.row_count} rows
                  {ds.period_start && ds.period_end && ` · ${formatPeriod(ds.period_start)} – ${formatPeriod(ds.period_end)}`}
                </p>
              </div>
              <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                ds.status === "completed" ? "text-risk-low bg-risk-low/10" :
                ds.status === "processing" ? "text-gold bg-gold/10" : "text-risk-high bg-risk-high/10"
              )}>
                {ds.status === "processing" ? <Loader2 size={10} className="animate-spin" /> :
                 ds.status === "completed" ? <CheckCircle size={10} /> : <AlertCircle size={10} />}
                {ds.status}
              </span>
              <button onClick={() => deleteMut.mutate(ds.id)} className="text-text-muted hover:text-risk-high"><Trash2 size={14} /></button>
            </div>
          ))}
        </div>
      )}

      {/* P&L Summary Table */}
      {summary && summary.periods.length > 0 && (
        <div className="card overflow-x-auto">
          <div className="px-4 py-3 border-b border-canvas-border">
            <h3 className="text-sm font-semibold text-text-primary">P&L Summary</h3>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-canvas-border bg-surface/50">
                <th className="px-4 py-2 text-left text-text-secondary font-medium">Category</th>
                {summary.periods.map((p) => (
                  <th key={p} className="px-3 py-2 text-right text-text-secondary font-medium">{formatPeriod(p)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {summary.categories.map((cat) => (
                <tr key={cat} className="border-b border-canvas-border/50 hover:bg-surface/30">
                  <td className="px-4 py-2 text-text-primary font-medium capitalize">{cat.replace(/_/g, " ")}</td>
                  {summary.periods.map((p) => {
                    const d = summary.data.find((r) => r.standardized_category === cat && r.period === p);
                    return <td key={p} className="px-3 py-2 text-right text-text-secondary font-mono">{d ? formatEur(d.amount) : "—"}</td>;
                  })}
                </tr>
              ))}
              {/* EBITDA row */}
              <tr className="border-t-2 border-gold/30 bg-gold/5">
                <td className="px-4 py-2 text-gold font-semibold">EBITDA</td>
                {summary.period_summaries.map((ps) => (
                  <td key={ps.period} className="px-3 py-2 text-right text-gold font-mono font-semibold">{formatEur(ps.ebitda)}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --- Variance Tab ---

function VarianceTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<"mom" | "yoy">("mom");

  const { data: variances = [], isLoading } = useQuery({
    queryKey: ["finance-variance", projectId, filter],
    queryFn: () => financeApi.getInternalVariance(projectId, { analysis_type: filter }),
  });

  const runMut = useMutation({
    mutationFn: () => financeApi.runAnalysis(projectId),
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ["finance-variance"] }), 3000);
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1 rounded border border-canvas-border overflow-hidden">
          {(["mom", "yoy"] as const).map((t) => (
            <button key={t} onClick={() => setFilter(t)}
              className={cn("px-3 py-1.5 text-xs font-medium transition-colors",
                filter === t ? "bg-gold text-canvas" : "bg-canvas-card text-text-secondary hover:bg-surface"
              )}>{t === "mom" ? "Month-over-Month" : "Year-over-Year"}</button>
          ))}
        </div>
        <button onClick={() => runMut.mutate()} className="btn-primary px-3 py-1.5 text-xs flex items-center gap-1.5" disabled={runMut.isPending}>
          <Play size={12} /> {runMut.isPending ? "Running..." : "Run Analysis"}
        </button>
      </div>

      {isLoading ? (
        <div className="card p-6 text-center"><Loader2 size={18} className="mx-auto animate-spin text-text-muted" /></div>
      ) : variances.length === 0 ? (
        <div className="card p-8 text-center">
          <BarChart3 size={28} className="mx-auto mb-3 text-text-muted" />
          <p className="text-sm text-text-secondary">No variance data yet. Import financial data and run analysis.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-canvas-border bg-surface/50">
                <th className="px-4 py-2 text-left text-text-secondary">Category</th>
                <th className="px-3 py-2 text-right text-text-secondary">Period</th>
                <th className="px-3 py-2 text-right text-text-secondary">vs.</th>
                <th className="px-3 py-2 text-right text-text-secondary">Change %</th>
                <th className="px-3 py-2 text-right text-text-secondary">Change EUR</th>
                <th className="px-3 py-2 text-center text-text-secondary">Significance</th>
              </tr>
            </thead>
            <tbody>
              {variances.map((v) => (
                <tr key={v.id} className="border-b border-canvas-border/50 hover:bg-surface/30">
                  <td className="px-4 py-2 text-text-primary font-medium capitalize">{(v.standardized_category || "").replace(/_/g, " ")}</td>
                  <td className="px-3 py-2 text-right text-text-secondary">{formatPeriod(v.period)}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{v.comparison_period ? formatPeriod(v.comparison_period) : "—"}</td>
                  <td className={cn("px-3 py-2 text-right font-mono", v.variance_pct && v.variance_pct > 0 ? "text-risk-low" : v.variance_pct && v.variance_pct < 0 ? "text-risk-high" : "text-text-muted")}>
                    {formatPct(v.variance_pct)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-text-secondary">{formatEur(v.variance_abs)}</td>
                  <td className="px-3 py-2 text-center">{significanceBadge(v.significance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --- Benchmarks Tab ---

function BenchmarksTab({ projectId }: { projectId: string }) {
  const { data: benchmarks = [], isLoading } = useQuery({
    queryKey: ["finance-benchmarks", projectId],
    queryFn: () => financeApi.getExternalBenchmarks(projectId),
  });

  if (isLoading) return <div className="card p-6 text-center"><Loader2 size={18} className="mx-auto animate-spin text-text-muted" /></div>;

  if (benchmarks.length === 0) return (
    <div className="card p-8 text-center">
      <BarChart3 size={28} className="mx-auto mb-3 text-text-muted" />
      <p className="text-sm text-text-secondary">No benchmark data available. Ensure the project has an industry set and financial data imported.</p>
    </div>
  );

  return (
    <div className="space-y-4">
      {benchmarks.map((b) => (
        <div key={b.metric_name} className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-text-primary capitalize">{b.metric_name.replace(/_/g, " ")}</p>
            <span className="text-[10px] text-text-muted">{b.source} ({b.year})</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gold">Company: {b.company_value.toFixed(1)}%</span>
                <span className="text-text-secondary">Industry: {b.industry_value.toFixed(1)}%</span>
              </div>
              <div className="h-2 rounded-full bg-surface overflow-hidden">
                <div className="h-full rounded-full bg-gold transition-all" style={{ width: `${Math.min(Math.max(b.company_value, 0), 100)}%` }} />
              </div>
              <div className="h-2 rounded-full bg-surface overflow-hidden mt-1">
                <div className="h-full rounded-full bg-text-muted transition-all" style={{ width: `${Math.min(Math.max(b.industry_value, 0), 100)}%` }} />
              </div>
            </div>
            <div className={cn("text-sm font-mono font-semibold px-3 py-1 rounded",
              b.delta > 0 ? "text-risk-low bg-risk-low/10" : "text-risk-high bg-risk-high/10"
            )}>
              {b.delta > 0 ? "+" : ""}{b.delta.toFixed(1)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// --- Queries Tab (HITL) ---

function QueriesTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const { data: queries = [], isLoading } = useQuery({
    queryKey: ["finance-queries", projectId],
    queryFn: () => financeApi.listQueries(projectId),
  });

  const reviewMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "approved" | "rejected" }) =>
      financeApi.reviewQuery(projectId, id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance-queries"] }),
  });

  if (isLoading) return <div className="card p-6 text-center"><Loader2 size={18} className="mx-auto animate-spin text-text-muted" /></div>;

  if (queries.length === 0) return (
    <div className="card p-8 text-center">
      <HelpCircle size={28} className="mx-auto mb-3 text-text-muted" />
      <p className="text-sm text-text-secondary">No queries generated yet. Run variance analysis first.</p>
    </div>
  );

  return (
    <div className="card divide-y divide-canvas-border">
      {queries.map((q) => (
        <div key={q.id} className="px-4 py-4 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <p className="text-sm text-text-primary flex-1">{q.question}</p>
            <span className={cn("shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
              q.status === "pending_review" ? "text-gold bg-gold/10" :
              q.status === "approved" ? "text-risk-low bg-risk-low/10" : "text-text-muted bg-surface"
            )}>{q.status.replace("_", " ")}</span>
          </div>
          {q.context && <p className="text-xs text-text-muted">{q.context}</p>}
          {q.status === "pending_review" && (
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => reviewMut.mutate({ id: q.id, status: "approved" })}
                className="inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-risk-low/10 text-risk-low hover:bg-risk-low/20 transition-colors"
              ><ThumbsUp size={11} /> Approve</button>
              <button
                onClick={() => reviewMut.mutate({ id: q.id, status: "rejected" })}
                className="inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-surface text-text-muted hover:bg-risk-high/10 hover:text-risk-high transition-colors"
              ><ThumbsDown size={11} /> Reject</button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// --- Main Page ---

const TABS = [
  { id: "overview", label: "Overview", icon: FileSpreadsheet },
  { id: "variance", label: "Variance Analysis", icon: BarChart3 },
  { id: "benchmarks", label: "Benchmarks", icon: TrendingUp },
  { id: "queries", label: "Queries", icon: HelpCircle },
] as const;

type TabId = typeof TABS[number]["id"];

export function FinancePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [tab, setTab] = useState<TabId>("overview");

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="font-display text-2xl text-text-primary">Financial Analysis</h1>
        <p className="mt-1 text-sm text-text-secondary">Import, analyze, and benchmark financial data</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-canvas-border">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors -mb-px",
                tab === t.id
                  ? "border-gold text-gold"
                  : "border-transparent text-text-muted hover:text-text-secondary"
              )}
            >
              <Icon size={13} /> {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {tab === "overview" && <OverviewTab projectId={projectId!} />}
      {tab === "variance" && <VarianceTab projectId={projectId!} />}
      {tab === "benchmarks" && <BenchmarksTab projectId={projectId!} />}
      {tab === "queries" && <QueriesTab projectId={projectId!} />}
    </div>
  );
}
