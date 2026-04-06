import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { finance } from '../../api/finance';
import { usePermissions } from '../../hooks/usePermissions';
import {
  TrendingUp, Upload, BarChart3, Loader2, FileSpreadsheet, AlertTriangle,
  ArrowUpRight, ArrowDownRight, Minus, Brain, FileText,
  AlertCircle, HelpCircle, Sparkles,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from 'recharts';

/** Format a number in German locale (1.234.567,89) */
function fmtDE(value: number | null | undefined, unit?: string): string {
  if (value == null) return '-';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: unit === '%' ? 1 : 0,
    maximumFractionDigits: unit === '%' ? 1 : 2,
  }).format(value);
  if (unit === 'EUR') return `€${formatted}`;
  if (unit === '%') return `${formatted}%`;
  return formatted;
}

/** Compact format for large EUR values */
function fmtCompact(value: number): string {
  if (Math.abs(value) >= 1_000_000) return `€${(value / 1_000_000).toFixed(1).replace('.', ',')}M`;
  if (Math.abs(value) >= 1_000) return `€${(value / 1_000).toFixed(0).replace('.', ',')}K`;
  return fmtDE(value, 'EUR');
}

const CHART_COLORS = ['#C9A84C', '#6366f1', '#22c55e', '#ef4444', '#f59e0b', '#8b5cf6'];

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-risk-high/10 text-risk-high border-risk-high/30',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  medium: 'bg-gold/10 text-gold border-gold/30',
  low: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  info: 'bg-surface text-secondary border-canvas-border',
};

export default function FinancePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const perms = usePermissions();
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'variance' | 'periods' | 'insights'>('overview');

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['finance-datasets', projectId],
    queryFn: () => finance.listDatasets(projectId!),
  });

  const { data: variances } = useQuery({
    queryKey: ['variance', projectId],
    queryFn: () => finance.getVarianceAnalyses(projectId!),
  });

  const { data: kpis } = useQuery({
    queryKey: ['finance-kpis', projectId],
    queryFn: () => finance.getKPIs(projectId!),
  });

  const { data: periodComparison } = useQuery({
    queryKey: ['period-comparison', projectId],
    queryFn: () => finance.getPeriodComparison(projectId!),
  });

  const { data: chartData } = useQuery({
    queryKey: ['chart-data', projectId],
    queryFn: () => finance.getChartData(projectId!),
  });

  // AI Insights
  const { data: latestInsight } = useQuery({
    queryKey: ['finance-insight', projectId],
    queryFn: () => finance.getLatestInsight(projectId!).catch(() => null),
  });

  const runAnalysis = useMutation({
    mutationFn: (type: string) => finance.runVarianceAnalysis(projectId!, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variance', projectId] });
      queryClient.invalidateQueries({ queryKey: ['chart-data', projectId] });
    },
  });

  const analyzeDocuments = useMutation({
    mutationFn: () => finance.analyzeDocuments(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance-insight', projectId] });
      queryClient.invalidateQueries({ queryKey: ['finance-kpis', projectId] });
      queryClient.invalidateQueries({ queryKey: ['chart-data', projectId] });
      setActiveTab('insights');
    },
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await finance.uploadData(projectId!, file);
      queryClient.invalidateQueries({ queryKey: ['finance-datasets', projectId] });
      queryClient.invalidateQueries({ queryKey: ['finance-kpis', projectId] });
      queryClient.invalidateQueries({ queryKey: ['period-comparison', projectId] });
    } finally {
      setUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-gold" />
          <h1 className="text-3xl font-display font-bold text-primary">Financial Analysis</h1>
        </div>
        <div className="flex items-center gap-3">
          {perms.canRunFinanceAnalysis && (
            <>
              <button
                className="btn-ghost text-sm px-3 py-1.5 flex items-center gap-1.5"
                onClick={() => analyzeDocuments.mutate()}
                disabled={analyzeDocuments.isPending}
              >
                {analyzeDocuments.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4" />
                )}
                {analyzeDocuments.isPending ? 'Analyzing...' : 'Analyze Data Room'}
              </button>
              <div className="flex gap-2">
                <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('internal_historical')}
                  disabled={runAnalysis.isPending || (!datasets?.length && !latestInsight)}>Internal Historical</button>
                <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('external_benchmark')}
                  disabled={runAnalysis.isPending || (!datasets?.length && !latestInsight)}>External Benchmark</button>
              </div>
            </>
          )}
          {perms.canUploadFinanceData && (
            <label className="btn-primary px-4 py-2 cursor-pointer flex items-center gap-2">
              <Upload className="w-4 h-4" />
              {uploading ? 'Uploading...' : 'Upload Data'}
              <input type="file" className="hidden" accept=".xlsx,.xls,.csv,.tsv" onChange={handleUpload} />
            </label>
          )}
        </div>
      </div>

      {/* AI Summary Banner */}
      {latestInsight?.summary && (
        <div className="card p-5 border-gold/30 bg-gold/5">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-gold shrink-0 mt-0.5" />
            <div>
              <p className="text-base font-medium text-gold mb-1">AI Financial Summary</p>
              <p className="text-base text-primary leading-relaxed">{latestInsight.summary}</p>
              <div className="flex items-center gap-4 mt-2 text-sm text-secondary">
                {latestInsight.source_document_ids?.length ? (
                  <span className="flex items-center gap-1">
                    <FileText className="w-3 h-3" /> {latestInsight.source_document_ids.length} document{latestInsight.source_document_ids.length > 1 ? 's' : ''} analysed
                  </span>
                ) : null}
                {latestInsight.source_dataset_ids?.length ? (
                  <span className="flex items-center gap-1">
                    <FileSpreadsheet className="w-3 h-3" /> {latestInsight.source_dataset_ids.length} dataset{latestInsight.source_dataset_ids.length > 1 ? 's' : ''} included
                  </span>
                ) : null}
                <span>{new Date(latestInsight.created_at).toLocaleString('de-DE')}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      {kpis && kpis.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {kpis.map((kpi) => (
            <div key={kpi.name + (kpi.period ?? '')} className="card p-5">
              <p className="text-sm text-secondary font-medium uppercase tracking-wide">{kpi.name}</p>
              <p className="text-2xl font-display font-bold text-primary mt-1">
                {fmtDE(kpi.value, kpi.unit)}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-1.5 py-0.5 rounded inline-block ${
                  kpi.category === 'profitability' ? 'bg-green-500/10 text-green-400' :
                  kpi.category === 'efficiency' ? 'bg-blue-500/10 text-blue-400' :
                  kpi.category === 'leverage' ? 'bg-orange-500/10 text-orange-400' :
                  'bg-gold/10 text-gold'
                }`}>{kpi.category}</span>
                {kpi.period && (
                  <span className="text-xs text-secondary">{kpi.period}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-6 text-center">
          <TrendingUp className="w-10 h-10 text-secondary/30 mx-auto mb-2" />
          <p className="text-secondary text-base">No financial KPIs available yet.</p>
          <p className="text-secondary text-sm mt-1">Upload financial data or click "Analyze Data Room" to extract metrics from documents.</p>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-canvas-border">
        {(['overview', 'variance', 'periods', 'insights'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-base font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
              activeTab === tab ? 'border-gold text-gold' : 'border-transparent text-secondary hover:text-primary'
            }`}>
            {tab === 'insights' && <Brain className="w-3.5 h-3.5" />}
            {tab === 'overview' ? 'Overview & Charts' : tab === 'variance' ? 'Variance Analysis' : tab === 'periods' ? 'Period Comparison' : 'AI Insights'}
            {tab === 'insights' && latestInsight?.anomalies?.length ? (
              <span className="text-xs bg-risk-high/20 text-risk-high rounded-full px-1.5 py-0.5 ml-1">
                {latestInsight.anomalies.length}
              </span>
            ) : null}
          </button>
        ))}
      </div>

      {/* Overview Tab - Charts */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Variance Bar Chart - from saved analysis or AI insight */}
          {(chartData?.variance?.length || latestInsight?.variance_results?.length) ? (
            <div className="card p-7">
              <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-gold" /> Current vs Prior Period
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={(chartData?.variance?.length ? chartData.variance : (latestInsight?.variance_results ?? []).map(r => ({
                    name: r.metric, current: r.current, prior: r.prior, variance_pct: r.variance_pct, flag: r.flag,
                  })))}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={(v) => fmtCompact(v)} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: 8 }}
                    labelStyle={{ color: '#C9A84C' }}
                    formatter={(value) => [fmtDE(value as number, 'EUR'), '']}
                  />
                  <Legend />
                  <Bar dataKey="current" name="Current" fill="#C9A84C" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="prior" name="Prior" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : null}

          {/* Trend Line Chart */}
          {chartData?.trends && chartData.trends.length > 0 && (
            <div className="card p-7">
              <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-gold" /> Multi-Period Trends
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="period"
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    allowDuplicatedCategory={false}
                  />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={(v) => fmtCompact(v)} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: 8 }}
                    formatter={(value) => [fmtDE(value as number, 'EUR'), '']}
                  />
                  <Legend />
                  {chartData.trends.slice(0, 5).map((trend, idx) => (
                    <Line
                      key={trend.metric}
                      data={trend.periods}
                      type="monotone"
                      dataKey="value"
                      name={trend.metric}
                      stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Datasets List */}
          <div className="card p-7 space-y-4">
            <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-gold" /> Imported Datasets
            </h2>
            {datasets?.length ? (
              <div className="space-y-3">
                {datasets.map(ds => (
                  <div key={ds.id} className="bg-surface p-4 rounded-lg border border-canvas-border flex items-center justify-between">
                    <div>
                      <p className="text-primary font-medium text-base">{ds.name}</p>
                      <p className="text-secondary text-sm mt-1">
                        {ds.chart_of_accounts && `${ds.chart_of_accounts} · `}
                        {ds.period_from && `${ds.period_from} - ${ds.period_to}`}
                        {!ds.period_from && 'Period not detected'}
                      </p>
                    </div>
                    <span className="text-sm text-secondary">{new Date(ds.created_at).toLocaleDateString('de-DE')}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileSpreadsheet className="w-14 h-14 text-secondary/30 mx-auto mb-3" />
                <p className="text-secondary font-medium text-base">No financial data uploaded yet</p>
                <p className="text-secondary text-sm mt-2 max-w-md mx-auto">
                  Upload Excel (.xlsx), CSV, or TSV files. German number format (1.234,56) is automatically detected.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Variance Analysis Tab */}
      {activeTab === 'variance' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gold" /> Variance Analysis
          </h2>
          {variances?.length ? (
            <div className="space-y-4">
              {variances.map(v => (
                <div key={v.id} className="bg-surface p-4 rounded-lg border border-canvas-border">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-primary font-medium capitalize">{v.analysis_type.replace('_', ' ')}</span>
                    <span className="text-xs text-secondary">{new Date(v.created_at).toLocaleDateString('de-DE')}</span>
                  </div>
                  {v.results?.length ? (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-canvas-border/50">
                          <th className="text-left p-2 text-secondary font-medium text-sm">Metric</th>
                          <th className="text-right p-2 text-secondary font-medium text-sm">Current</th>
                          <th className="text-right p-2 text-secondary font-medium text-sm">Prior</th>
                          <th className="text-right p-2 text-secondary font-medium text-sm">Variance</th>
                          <th className="text-center p-2 text-secondary font-medium text-sm">Flag</th>
                        </tr>
                      </thead>
                      <tbody>
                        {v.results.map((r: { metric?: string; label?: string; current?: number; prior?: number; variance_pct?: number; flag?: string }, i: number) => (
                          <tr key={i} className="border-b border-canvas-border/30">
                            <td className="p-2 text-primary">{r.metric || r.label || `Item ${i+1}`}</td>
                            <td className="p-2 text-primary text-right">{fmtDE(r.current, 'EUR')}</td>
                            <td className="p-2 text-secondary text-right">{fmtDE(r.prior, 'EUR')}</td>
                            <td className="p-2 text-right">
                              <span className={`flex items-center justify-end gap-1 ${
                                r.flag === 'significant' ? 'text-risk-high' : 'text-primary'
                              }`}>
                                {(r.variance_pct ?? 0) > 0 ? <ArrowUpRight className="w-3 h-3" /> :
                                 (r.variance_pct ?? 0) < 0 ? <ArrowDownRight className="w-3 h-3" /> :
                                 <Minus className="w-3 h-3" />}
                                {fmtDE(r.variance_pct, '%')}
                              </span>
                            </td>
                            <td className="p-2 text-center">
                              {r.flag === 'significant' ? (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-risk-high/10 text-risk-high">Significant</span>
                              ) : (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-risk-low/10 text-risk-low">Normal</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-secondary text-base italic">Analysis pending.</p>
                  )}
                  {v.generated_queries?.length ? (
                    <div className="mt-3 pt-3 border-t border-canvas-border/50">
                      <p className="text-gold text-xs font-medium mb-1 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> AI-Generated Follow-up Queries
                      </p>
                      {v.generated_queries.map((q: string | { question?: string }, i: number) => (
                        <p key={i} className="text-secondary text-xs">• {typeof q === 'string' ? q : q.question || JSON.stringify(q)}</p>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-14 h-14 text-secondary/30 mx-auto mb-3" />
              <p className="text-secondary text-base">No variance analysis run yet.</p>
              <p className="text-secondary text-sm mt-1">Upload data or run "Analyze Data Room", then trigger variance analysis.</p>
            </div>
          )}
        </div>
      )}

      {/* Period Comparison Tab */}
      {activeTab === 'periods' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gold" /> Period Comparison
          </h2>
          {periodComparison?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-canvas-border">
                    <th className="text-left p-3 text-secondary font-medium text-sm">Metric</th>
                    {periodComparison[0]?.periods?.map((p, i) => (
                      <th key={i} className="text-right p-3 text-secondary font-medium text-sm">{p.period}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {periodComparison.map((row) => (
                    <tr key={row.metric} className="border-b border-canvas-border/30">
                      <td className="p-3 text-primary font-medium">{row.metric}</td>
                      {row.periods.map((p, i) => (
                        <td key={i} className="p-3 text-right">
                          <div className="text-primary">{fmtDE(p.value, 'EUR')}</div>
                          {p.change_pct !== undefined && (
                            <span className={`text-xs flex items-center justify-end gap-0.5 mt-0.5 ${
                              p.change_pct > 0 ? 'text-green-400' : p.change_pct < 0 ? 'text-risk-high' : 'text-secondary'
                            }`}>
                              {p.change_pct > 0 ? <ArrowUpRight className="w-3 h-3" /> :
                               p.change_pct < 0 ? <ArrowDownRight className="w-3 h-3" /> :
                               <Minus className="w-3 h-3" />}
                              {fmtDE(p.change_pct, '%')}
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-14 h-14 text-secondary/30 mx-auto mb-3" />
              <p className="text-secondary text-base">No period comparison data available yet.</p>
              <p className="text-secondary text-sm mt-1">Upload multiple datasets to compare across periods.</p>
            </div>
          )}
        </div>
      )}

      {/* AI Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          {!latestInsight ? (
            <div className="card p-10 text-center">
              <Brain className="w-18 h-18 text-secondary/20 mx-auto mb-4" />
              <h3 className="text-primary font-display text-xl mb-2">No AI Analysis Yet</h3>
              <p className="text-secondary text-base max-w-md mx-auto mb-4">
                Click "Analyze Data Room" to have AI extract financial figures from your documents,
                compute KPIs, identify variances, and flag anomalies.
              </p>
              {perms.canRunFinanceAnalysis && (
                <button
                  className="btn-primary px-6 py-2.5 inline-flex items-center gap-2"
                  onClick={() => analyzeDocuments.mutate()}
                  disabled={analyzeDocuments.isPending}
                >
                  {analyzeDocuments.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                  {analyzeDocuments.isPending ? 'Analyzing...' : 'Analyze Data Room'}
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Anomalies / Follow-up Questions */}
              {latestInsight.anomalies && latestInsight.anomalies.length > 0 && (
                <div className="card p-7 space-y-4">
                  <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-gold" />
                    Anomalies &amp; Follow-up Questions
                    <span className="text-xs bg-risk-high/10 text-risk-high rounded-full px-2 py-0.5 ml-2">
                      {latestInsight.anomalies.length} item{latestInsight.anomalies.length > 1 ? 's' : ''}
                    </span>
                  </h2>
                  <div className="space-y-3">
                    {latestInsight.anomalies.map((a, i) => (
                      <div key={i} className={`p-4 rounded-lg border ${SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.info}`}>
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-medium uppercase tracking-wide">{a.severity}</span>
                              <span className="text-xs opacity-60">- {a.metric}</span>
                            </div>
                            <p className="text-base font-medium">{a.question}</p>
                            {a.detail && (
                              <p className="text-sm opacity-70 mt-1">{a.detail}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI-Extracted Variance */}
              {latestInsight.variance_results && latestInsight.variance_results.length > 0 && (
                <div className="card p-7 space-y-4">
                  <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-gold" /> AI-Detected Variance
                  </h2>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-canvas-border/50">
                        <th className="text-left p-2 text-secondary font-medium text-sm">Metric</th>
                        <th className="text-right p-2 text-secondary font-medium text-sm">Current</th>
                        <th className="text-right p-2 text-secondary font-medium text-sm">Prior</th>
                        <th className="text-right p-2 text-secondary font-medium text-sm">Periods</th>
                        <th className="text-right p-2 text-secondary font-medium text-sm">Variance</th>
                        <th className="text-center p-2 text-secondary font-medium text-sm">Flag</th>
                      </tr>
                    </thead>
                    <tbody>
                      {latestInsight.variance_results.map((r, i) => (
                        <tr key={i} className="border-b border-canvas-border/30">
                          <td className="p-2 text-primary font-medium">{r.metric}</td>
                          <td className="p-2 text-primary text-right">{fmtDE(r.current, 'EUR')}</td>
                          <td className="p-2 text-secondary text-right">{fmtDE(r.prior, 'EUR')}</td>
                          <td className="p-2 text-secondary text-right text-xs">{r.current_period} vs {r.prior_period}</td>
                          <td className="p-2 text-right">
                            <span className={`flex items-center justify-end gap-1 ${
                              r.flag === 'significant' ? 'text-risk-high' : 'text-primary'
                            }`}>
                              {r.variance_pct > 0 ? <ArrowUpRight className="w-3 h-3" /> :
                               r.variance_pct < 0 ? <ArrowDownRight className="w-3 h-3" /> :
                               <Minus className="w-3 h-3" />}
                              {fmtDE(r.variance_pct, '%')}
                            </span>
                          </td>
                          <td className="p-2 text-center">
                            {r.flag === 'significant' ? (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-risk-high/10 text-risk-high">Significant</span>
                            ) : (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-risk-low/10 text-risk-low">Normal</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* AI-Extracted Figures */}
              {latestInsight.extracted_figures && latestInsight.extracted_figures.length > 0 && (
                <div className="card p-7 space-y-4">
                  <h2 className="text-xl font-display font-semibold text-primary flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gold" /> Extracted Financial Figures
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-canvas-border/50">
                          <th className="text-left p-2 text-secondary font-medium text-sm">Metric</th>
                          <th className="text-right p-2 text-secondary font-medium text-sm">Value</th>
                          <th className="text-center p-2 text-secondary font-medium text-sm">Period</th>
                          <th className="text-left p-2 text-secondary font-medium text-sm">Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestInsight.extracted_figures.map((f, i) => (
                          <tr key={i} className="border-b border-canvas-border/30">
                            <td className="p-2 text-primary">{f.metric}</td>
                            <td className="p-2 text-primary text-right font-mono">
                              {f.currency === 'EUR' || !f.currency ? fmtDE(f.value, 'EUR') : `${f.value.toLocaleString()} ${f.currency}`}
                            </td>
                            <td className="p-2 text-center text-secondary text-xs">{f.period}</td>
                            <td className="p-2 text-secondary text-xs truncate max-w-[200px]">{f.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
