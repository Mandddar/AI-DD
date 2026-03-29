import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reports, type ReportCreate } from '../../api/reports';
import {
  FileText, Plus, Download, CheckCircle2, Edit3, Loader2, Lock
} from 'lucide-react';

const REPORT_TYPES = [
  { value: 'detailed_workstream', label: 'Detailed Workstream Report' },
  { value: 'executive_summary', label: 'Executive Summary' },
  { value: 'consolidated', label: 'Consolidated Overall Report' },
];

export default function ReportsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ReportCreate>({
    report_type: 'detailed_workstream',
    workstream: 'legal',
    title: '',
  });

  const { data: reportList, isLoading } = useQuery({
    queryKey: ['reports', projectId],
    queryFn: () => reports.list(projectId!),
  });

  const generate = useMutation({
    mutationFn: () => reports.generate(projectId!, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] });
      setShowForm(false);
      setFormData({ report_type: 'detailed_workstream', workstream: 'legal', title: '' });
    },
  });

  const finalize = useMutation({
    mutationFn: (reportId: string) => reports.finalize(projectId!, reportId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports', projectId] }),
  });

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
          <FileText className="w-7 h-7 text-gold" />
          <h1 className="text-2xl font-display font-bold text-primary">Reports</h1>
        </div>
        <button className="btn-primary px-4 py-2 flex items-center gap-2" onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4" /> Generate Report
        </button>
      </div>

      {/* Generate Form */}
      {showForm && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary">New Report</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Report Type</label>
              <select className="input w-full" value={formData.report_type}
                onChange={e => setFormData(d => ({ ...d, report_type: e.target.value }))}>
                {REPORT_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            {formData.report_type === 'detailed_workstream' && (
              <div>
                <label className="label">Workstream</label>
                <select className="input w-full" value={formData.workstream}
                  onChange={e => setFormData(d => ({ ...d, workstream: e.target.value }))}>
                  <option value="legal">Legal</option>
                  <option value="tax">Tax</option>
                  <option value="finance">Finance</option>
                </select>
              </div>
            )}
            <div>
              <label className="label">Title</label>
              <input className="input w-full" placeholder="Report title" value={formData.title}
                onChange={e => setFormData(d => ({ ...d, title: e.target.value }))} />
            </div>
          </div>
          <button className="btn-primary px-6 py-2" onClick={() => generate.mutate()}
            disabled={generate.isPending || !formData.title}>
            {generate.isPending ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      )}

      {/* Report List */}
      {reportList?.length ? (
        <div className="space-y-4">
          {reportList.map(report => (
            <div key={report.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <FileText className={`w-5 h-5 mt-0.5 ${report.is_finalized ? 'text-green-400' : 'text-gold'}`} />
                  <div>
                    <h3 className="text-primary font-medium">{report.title}</h3>
                    <p className="text-secondary text-sm mt-1">
                      {REPORT_TYPES.find(t => t.value === report.report_type)?.label}
                      {report.workstream && ` · ${report.workstream}`}
                    </p>
                    <p className="text-secondary/60 text-xs mt-1">{new Date(report.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {report.is_finalized ? (
                    <span className="flex items-center gap-1 text-green-400 text-xs">
                      <Lock className="w-3 h-3" /> Finalized
                    </span>
                  ) : (
                    <>
                      <button className="btn-ghost text-xs px-3 py-1.5 flex items-center gap-1">
                        <Edit3 className="w-3 h-3" /> Edit
                      </button>
                      <button className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                        onClick={() => finalize.mutate(report.id)}>
                        <CheckCircle2 className="w-3 h-3" /> Finalize
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <FileText className="w-16 h-16 text-secondary/20 mx-auto mb-4" />
          <h3 className="text-primary font-display text-lg mb-2">No Reports Yet</h3>
          <p className="text-secondary text-sm">Generate your first report after completing AI analysis.</p>
        </div>
      )}

      {/* AI Disclaimer */}
      <div className="text-xs text-secondary/60 italic border-t border-canvas-border/30 pt-4">
        Notice: AI-generated report content may be inaccurate, incomplete, or misleading.
        All reports require human review before distribution. This tool does not replace qualified advisory services.
      </div>
    </div>
  );
}
