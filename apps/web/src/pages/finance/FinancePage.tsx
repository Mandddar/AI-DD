import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { finance } from '../../api/finance';
import { usePermissions } from '../../hooks/usePermissions';
import {
  TrendingUp, Upload, BarChart3, Loader2, FileSpreadsheet, AlertTriangle,
  TrendingDown, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, Cell,
} from 'recharts';

/** Format a number in German locale (1.234.567,89) */
function fmtDE(value: number | null | undefined, unit?: string): string {
  if (value == null) return '—';
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

export default function FinancePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const perms = usePermissions();
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'variance' | 'periods'>('overview');

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

  const runAnalysis = useMutation({
    mutationFn: (type: string) => finance.runVarianceAnalysis(projectId!, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['variance', projectId] });
      queryClient.invalidateQueries({ queryKey: ['chart-data', projectId] });
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-7 h-7 text-gold" />
          <h1 className="text-2xl font-display font-bold text-primary">Financial Analysis</h1>
        </div>
        <div className="flex items-center gap-3">
          {perms.canRunFinanceAnalysis && (
            <div className="flex gap-2">
              <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('internal_historical')}
                disabled={runAnalysis.isPending || !datasets?.length}>Internal Historical</button>
              <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('external_benchmark')}
                disabled={runAnalysis.isPending || !datasets?.length}>External Benchmark</button>
            </div>
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

      {/* KPI Cards */}
      {kpis && kpis.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {kpis.map((kpi) => (
            <div key={kpi.name} className="card p-4">
              <p className="text-xs text-secondary font-medium uppercase tracking-wide">{kpi.name}</p>
              <p className="text-xl font-display font-bold text-primary mt-1">
                {fmtDE(kpi.value, kpi.unit)}
              </p>
              <span className={`text-[10px] px-1.5 py-0.5 rounded mt-2 inline-block ${
                kpi.category === 'profitability' ? 'bg-green-500/10 text-green-400' :
                kpi.category === 'efficiency' ? 'bg-blue-500/10 text-blue-400' :
                kpi.category === 'leverage' ? 'bg-orange-500/10 text-orange-400' :
                'bg-gold/10 text-gold'
              }`}>{kpi.category}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-canvas-border">
        {(['overview', 'variance', 'periods'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab ? 'border-gold text-gold' : 'border-transparent text-secondary hover:text-primary'
            }`}>
            {tab === 'overview' ? 'Overview & Charts' : tab === 'variance' ? 'Variance Analysis' : 'Period Comparison'}
          </button>
        ))}
      </div>

      {/* Overview Tab - Charts */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Variance Bar Chart */}
          {chartData?.variance && chartData.variance.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-gold" /> Current vs Prior Period
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData.variance} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={(v) => fmtCompact(v)} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: 8 }}
                    labelStyle={{ color: '#C9A84C' }}
                    formatter={(value: number) => [fmtDE(value, 'EUR'), '']}
                  />
                  <Legend />
                  <Bar dataKey="current" name="Current" fill="#C9A84C" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="prior" name="Prior" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Trend Line Chart */}
          {chartData?.trends && chartData.trends.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2 mb-4">
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
                    formatter={(value: number) => [fmtDE(value, 'EUR'), '']}
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
          <div className="card p-6 space-y-4">
            <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-gold" /> Imported Datasets
            </h2>
            {datasets?.length ? (
              <div className="space-y-3">
                {datasets.map(ds => (
                  <div key={ds.id} className="bg-surface p-4 rounded-lg border border-canvas-border flex items-center justify-between">
                    <div>
                      <p className="text-primary font-medium">{ds.name}</p>
                      <p className="text-secondary text-xs mt-1">
                        {ds.chart_of_accounts && `${ds.chart_of_accounts} · `}
                        {ds.period_from && `${ds.period_from} — ${ds.period_to}`}
                        {!ds.period_from && 'Period not detected'}
                      </p>
                    </div>
                    <span className="text-xs text-secondary">{new Date(ds.created_at).toLocaleDateString('de-DE')}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileSpreadsheet className="w-12 h-12 text-secondary/30 mx-auto mb-3" />
                <p className="text-secondary font-medium">No financial data uploaded yet</p>
                <p className="text-secondary/60 text-sm mt-2 max-w-md mx-auto">
                  Upload Excel (.xlsx), CSV, or TSV files. German number format (1.234,56) is automatically detected.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Variance Analysis Tab */}
      {activeTab === 'variance' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2">
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
                          <th className="text-left p-2 text-secondary font-medium">Metric</th>
                          <th className="text-right p-2 text-secondary font-medium">Current</th>
                          <th className="text-right p-2 text-secondary font-medium">Prior</th>
                          <th className="text-right p-2 text-secondary font-medium">Variance</th>
                          <th className="text-center p-2 text-secondary font-medium">Flag</th>
                        </tr>
                      </thead>
                      <tbody>
                        {v.results.map((r: any, i: number) => (
                          <tr key={i} className="border-b border-canvas-border/30">
                            <td className="p-2 text-primary">{r.metric || r.label || `Item ${i+1}`}</td>
                            <td className="p-2 text-primary text-right">{fmtDE(r.current, 'EUR')}</td>
                            <td className="p-2 text-secondary text-right">{fmtDE(r.prior, 'EUR')}</td>
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
                  ) : (
                    <p className="text-secondary text-sm italic">Analysis pending.</p>
                  )}
                  {v.generated_queries?.length ? (
                    <div className="mt-3 pt-3 border-t border-canvas-border/50">
                      <p className="text-gold text-xs font-medium mb-1 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> AI-Generated Follow-up Queries
                      </p>
                      {v.generated_queries.map((q: any, i: number) => (
                        <p key={i} className="text-secondary text-xs">• {typeof q === 'string' ? q : q.question || JSON.stringify(q)}</p>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-secondary/30 mx-auto mb-3" />
              <p className="text-secondary">No variance analysis run yet.</p>
              <p className="text-secondary/60 text-sm mt-1">Upload financial data first, then run analysis.</p>
            </div>
          )}
        </div>
      )}

      {/* Period Comparison Tab */}
      {activeTab === 'periods' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gold" /> Period Comparison
          </h2>
          {periodComparison?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-canvas-border">
                    <th className="text-left p-3 text-secondary font-medium">Metric</th>
                    {periodComparison[0]?.periods?.map((p, i) => (
                      <th key={i} className="text-right p-3 text-secondary font-medium">{p.period}</th>
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
              <TrendingUp className="w-12 h-12 text-secondary/30 mx-auto mb-3" />
              <p className="text-secondary">No period comparison data available yet.</p>
              <p className="text-secondary/60 text-sm mt-1">Upload multiple datasets to compare across periods.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
