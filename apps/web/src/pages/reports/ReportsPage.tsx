import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reports, type ReportCreate, type Report } from '../../api/reports';
import {
  FileText, Plus, Download, CheckCircle2, Edit3, Loader2, Lock, Eye, X, Save
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
  const [viewReport, setViewReport] = useState<Report | null>(null);
  const [editReport, setEditReport] = useState<Report | null>(null);
  const [editText, setEditText] = useState('');
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

  const saveEdit = useMutation({
    mutationFn: () => {
      if (!editReport) throw new Error('No report selected');
      let parsed: Record<string, any>;
      try {
        parsed = JSON.parse(editText);
      } catch {
        parsed = { content: editText };
      }
      return reports.editContent(projectId!, editReport.id, parsed);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] });
      setEditReport(null);
    },
  });

  const handleEdit = (report: Report) => {
    const content = report.edited_content || report.content || {};
    setEditText(JSON.stringify(content, null, 2));
    setEditReport(report);
  };

  const handleDownload = (report: Report) => {
    const url = reports.downloadUrl(projectId!, report.id);
    const token = localStorage.getItem('access_token');
    // Use fetch with auth header, then trigger download
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        if (!res.ok) throw new Error('Download failed');
        return res.blob();
      })
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        const safe = report.title.replace(/[^a-zA-Z0-9 _-]/g, '_');
        a.download = `${safe}.docx`;
        a.click();
        URL.revokeObjectURL(a.href);
      })
      .catch(err => alert(err.message));
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
                  {/* View button — always available */}
                  <button className="btn-ghost text-xs px-3 py-1.5 flex items-center gap-1"
                    onClick={() => setViewReport(report)}>
                    <Eye className="w-3 h-3" /> View
                  </button>

                  {report.is_finalized ? (
                    <>
                      <span className="flex items-center gap-1 text-green-400 text-xs">
                        <Lock className="w-3 h-3" /> Finalized
                      </span>
                      <button className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                        onClick={() => handleDownload(report)}>
                        <Download className="w-3 h-3" /> Download
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn-ghost text-xs px-3 py-1.5 flex items-center gap-1"
                        onClick={() => handleEdit(report)}>
                        <Edit3 className="w-3 h-3" /> Edit
                      </button>
                      <button className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                        onClick={() => finalize.mutate(report.id)}
                        disabled={finalize.isPending}>
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

      {/* View Modal */}
      {viewReport && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setViewReport(null)}>
          <div className="bg-canvas-card border border-canvas-border rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b border-canvas-border">
              <div>
                <h2 className="text-lg font-display font-semibold text-primary">{viewReport.title}</h2>
                <p className="text-secondary text-xs mt-1">
                  {REPORT_TYPES.find(t => t.value === viewReport.report_type)?.label}
                  {viewReport.workstream && ` · ${viewReport.workstream}`}
                </p>
              </div>
              <button onClick={() => setViewReport(null)} className="text-secondary hover:text-primary">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 overflow-y-auto flex-1">
              {(() => {
                const content = viewReport.edited_content || viewReport.content || {};
                if (Object.keys(content).length === 0) {
                  return <p className="text-secondary italic">No content generated yet. Run AI analysis first, then generate report.</p>;
                }
                return (
                  <div className="space-y-4">
                    {Object.entries(content).map(([key, value]) => (
                      <div key={key}>
                        <h3 className="text-gold font-medium text-sm mb-1">{key}</h3>
                        <p className="text-secondary text-sm whitespace-pre-wrap">
                          {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                        </p>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
            <div className="p-4 border-t border-canvas-border text-xs text-secondary/60 italic">
              Notice: AI-generated content may be inaccurate. Human review is required before distribution.
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editReport && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setEditReport(null)}>
          <div className="bg-canvas-card border border-canvas-border rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b border-canvas-border">
              <div>
                <h2 className="text-lg font-display font-semibold text-primary">Edit: {editReport.title}</h2>
                <p className="text-secondary text-xs mt-1">Edit the report content below. Use JSON format for structured content, or plain text.</p>
              </div>
              <button onClick={() => setEditReport(null)} className="text-secondary hover:text-primary">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 flex-1 overflow-y-auto">
              <textarea
                className="input w-full h-80 font-mono text-sm resize-none"
                value={editText}
                onChange={e => setEditText(e.target.value)}
              />
            </div>
            <div className="p-4 border-t border-canvas-border flex justify-end gap-3">
              <button className="btn-ghost px-4 py-2 text-sm" onClick={() => setEditReport(null)}>Cancel</button>
              <button className="btn-primary px-4 py-2 text-sm flex items-center gap-2"
                onClick={() => saveEdit.mutate()}
                disabled={saveEdit.isPending}>
                <Save className="w-4 h-4" />
                {saveEdit.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
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
