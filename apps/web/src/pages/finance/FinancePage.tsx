import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { finance } from '../../api/finance';
import { usePermissions } from '../../hooks/usePermissions';
import {
  TrendingUp, Upload, BarChart3, Loader2, FileSpreadsheet, AlertTriangle
} from 'lucide-react';

export default function FinancePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const perms = usePermissions();
  const [uploading, setUploading] = useState(false);

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['finance-datasets', projectId],
    queryFn: () => finance.listDatasets(projectId!),
  });

  const { data: variances } = useQuery({
    queryKey: ['variance', projectId],
    queryFn: () => finance.getVarianceAnalyses(projectId!),
  });

  const runAnalysis = useMutation({
    mutationFn: (type: string) => finance.runVarianceAnalysis(projectId!, type),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['variance', projectId] }),
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await finance.uploadData(projectId!, file);
      queryClient.invalidateQueries({ queryKey: ['finance-datasets', projectId] });
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
        {perms.canUploadFinanceData && (
          <label className="btn-primary px-4 py-2 cursor-pointer flex items-center gap-2">
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploading...' : 'Upload Financial Data'}
            <input type="file" className="hidden" accept=".xlsx,.xls,.csv,.tsv" onChange={handleUpload} />
          </label>
        )}
      </div>

      {/* Datasets */}
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
                <span className="text-xs text-secondary">{new Date(ds.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FileSpreadsheet className="w-12 h-12 text-secondary/30 mx-auto mb-3" />
            <p className="text-secondary">No financial data uploaded yet.</p>
            <p className="text-secondary/60 text-sm mt-1">Upload Excel (.xlsx) or TSV files to begin analysis.</p>
          </div>
        )}
      </div>

      {/* Variance Analysis */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-semibold text-primary flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gold" /> Variance Analysis
          </h2>
          {perms.canRunFinanceAnalysis && (
            <div className="flex gap-2">
              <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('internal_historical')}
                disabled={runAnalysis.isPending || !datasets?.length}
                title={!datasets?.length ? 'Upload financial data first' : ''}>Internal Historical</button>
              <button className="btn-ghost text-sm px-3 py-1.5" onClick={() => runAnalysis.mutate('external_benchmark')}
                disabled={runAnalysis.isPending || !datasets?.length}
                title={!datasets?.length ? 'Upload financial data first' : ''}>External Benchmark</button>
            </div>
          )}
        </div>
        {variances?.length ? (
          <div className="space-y-3">
            {variances.map(v => (
              <div key={v.id} className="bg-surface p-4 rounded-lg border border-canvas-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-primary font-medium capitalize">{v.analysis_type.replace('_', ' ')}</span>
                  <span className="text-xs text-secondary">{new Date(v.created_at).toLocaleDateString()}</span>
                </div>
                {v.results?.length ? (
                  <div className="space-y-1 text-sm">
                    {v.results.slice(0, 5).map((r: any, i: number) => (
                      <div key={i} className="flex justify-between text-secondary">
                        <span>{r.metric || r.label || `Item ${i+1}`}</span>
                        <span className={r.flag === 'significant' ? 'text-risk-high' : ''}>{r.variance_pct || '—'}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-secondary text-sm italic">Analysis pending — results will appear when the Finance Agent completes processing.</p>
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
    </div>
  );
}
