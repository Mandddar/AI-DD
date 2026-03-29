import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { planning, type BasicDataInput, type RequestItem } from '../../api/planning';
import {
  ClipboardList, Building2, AlertTriangle, MessageSquare,
  CheckCircle2, FileSpreadsheet, ChevronRight, Loader2
} from 'lucide-react';

const PHASES = [
  { key: 'basic_data', label: 'Basic Data', icon: Building2 },
  { key: 'risk_analysis', label: 'Risk Analysis', icon: AlertTriangle },
  { key: 'dialog', label: 'Interactive Dialog', icon: MessageSquare },
  { key: 'plan_approval', label: 'Plan Approval', icon: CheckCircle2 },
  { key: 'request_list', label: 'Request List', icon: FileSpreadsheet },
];

export default function PlanningPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  const { data: plan, isLoading } = useQuery({
    queryKey: ['planning', projectId],
    queryFn: () => planning.getPlan(projectId!),
    retry: false,
  });

  const { data: requestItems } = useQuery({
    queryKey: ['requestList', projectId],
    queryFn: () => planning.getRequestList(projectId!),
    enabled: plan?.current_phase === 'request_list',
  });

  const [formData, setFormData] = useState<BasicDataInput>({
    company_name: '',
    legal_form: 'GmbH',
    registered_office: '',
    industry: '',
    employee_count: 0,
    revenue_size: '',
    deal_type: 'share_deal',
  });

  const submitBasicData = useMutation({
    mutationFn: () => planning.submitBasicData(projectId!, formData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['planning', projectId] }),
  });

  const advancePhase = useMutation({
    mutationFn: () => planning.advancePhase(projectId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['planning', projectId] }),
  });

  const approvePlan = useMutation({
    mutationFn: () => planning.approvePlan(projectId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['planning', projectId] }),
  });

  const updateItem = useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: Partial<RequestItem> }) =>
      planning.updateRequestItem(projectId!, itemId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['requestList', projectId] }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  const currentPhaseIdx = plan ? PHASES.findIndex(p => p.key === plan.current_phase) : -1;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <ClipboardList className="w-7 h-7 text-gold" />
        <h1 className="text-2xl font-display font-bold text-primary">Audit Planning</h1>
      </div>

      {/* Phase Stepper */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          {PHASES.map((phase, idx) => {
            const Icon = phase.icon;
            const isActive = idx === currentPhaseIdx;
            const isCompleted = idx < currentPhaseIdx;
            return (
              <div key={phase.key} className="flex items-center gap-2 flex-1">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                  isActive ? 'bg-gold/10 text-gold border border-gold/30' :
                  isCompleted ? 'text-green-400' : 'text-secondary'
                }`}>
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium hidden lg:inline">{phase.label}</span>
                </div>
                {idx < PHASES.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-secondary/40 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* No Plan Yet — Show Phase 1 Form */}
      {!plan && (
        <div className="card p-6 space-y-6">
          <h2 className="text-lg font-display font-semibold text-primary">Phase 1 — Basic Company Data</h2>
          <p className="text-secondary text-sm">Enter the target company's basic information to begin the audit planning process.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Company Name *</label>
              <input className="input w-full" value={formData.company_name}
                onChange={e => setFormData(d => ({ ...d, company_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Legal Form *</label>
              <select className="input w-full" value={formData.legal_form}
                onChange={e => setFormData(d => ({ ...d, legal_form: e.target.value }))}>
                <option value="GmbH">GmbH</option>
                <option value="AG">AG</option>
                <option value="KG">KG</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="label">Registered Office *</label>
              <input className="input w-full" value={formData.registered_office}
                onChange={e => setFormData(d => ({ ...d, registered_office: e.target.value }))} />
            </div>
            <div>
              <label className="label">Industry *</label>
              <input className="input w-full" value={formData.industry}
                onChange={e => setFormData(d => ({ ...d, industry: e.target.value }))} />
            </div>
            <div>
              <label className="label">Employee Count *</label>
              <input className="input w-full" type="number" value={formData.employee_count}
                onChange={e => setFormData(d => ({ ...d, employee_count: parseInt(e.target.value) || 0 }))} />
            </div>
            <div>
              <label className="label">Revenue Size *</label>
              <input className="input w-full" placeholder="e.g. €5M - €10M" value={formData.revenue_size}
                onChange={e => setFormData(d => ({ ...d, revenue_size: e.target.value }))} />
            </div>
            <div>
              <label className="label">Deal Type *</label>
              <select className="input w-full" value={formData.deal_type}
                onChange={e => setFormData(d => ({ ...d, deal_type: e.target.value }))}>
                <option value="share_deal">Share Deal</option>
                <option value="asset_deal">Asset Deal</option>
              </select>
            </div>
          </div>
          <button className="btn-primary px-6 py-2" onClick={() => submitBasicData.mutate()}
            disabled={submitBasicData.isPending || !formData.company_name}>
            {submitBasicData.isPending ? 'Submitting...' : 'Start Audit Planning'}
          </button>
        </div>
      )}

      {/* Phase 2 — Risk Analysis */}
      {plan?.current_phase === 'risk_analysis' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary">Phase 2 — AI Risk Analysis</h2>
          <p className="text-secondary text-sm">AI-derived risk areas based on company profile.</p>
          {plan.risk_analysis?.length ? (
            <div className="space-y-3">
              {plan.risk_analysis.map((risk: any, i: number) => (
                <div key={i} className="bg-surface p-4 rounded-lg border border-canvas-border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-primary">{risk.risk_area || risk.title}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      risk.severity === 'high' ? 'bg-risk-high/10 text-risk-high' :
                      risk.severity === 'medium' ? 'bg-risk-medium/10 text-risk-medium' :
                      'bg-risk-low/10 text-risk-low'
                    }`}>{risk.severity}</span>
                  </div>
                  <p className="text-secondary text-sm">{risk.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary italic">Risk analysis is being generated...</p>
          )}
          <button className="btn-primary px-6 py-2" onClick={() => advancePhase.mutate()}
            disabled={advancePhase.isPending}>
            {advancePhase.isPending ? 'Processing...' : 'Proceed to Interactive Dialog'}
          </button>
        </div>
      )}

      {/* Phase 3 — Interactive Dialog */}
      {plan?.current_phase === 'dialog' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary">Phase 3 — Interactive Dialog</h2>
          <p className="text-secondary text-sm">AI asks targeted follow-up questions based on the risk analysis.</p>
          {plan.dialog_history?.length ? (
            <div className="space-y-3">
              {plan.dialog_history.map((item: any, i: number) => (
                <div key={i} className="bg-surface p-4 rounded-lg border border-canvas-border">
                  <p className="text-gold text-sm font-medium mb-1">Q: {item.question}</p>
                  <p className="text-primary text-sm">A: {item.answer || '—'}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary italic">No dialog questions generated yet.</p>
          )}
          <button className="btn-primary px-6 py-2" onClick={() => advancePhase.mutate()}
            disabled={advancePhase.isPending}>
            {advancePhase.isPending ? 'Processing...' : 'Proceed to Plan Approval'}
          </button>
        </div>
      )}

      {/* Phase 4 — Audit Plan Approval */}
      {plan?.current_phase === 'plan_approval' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary">Phase 4 — Audit Plan Approval</h2>
          <p className="text-secondary text-sm">Review the generated audit plan. Specialized agents will only begin work after your approval.</p>
          {plan.audit_plan_content ? (
            <pre className="bg-surface p-4 rounded-lg border border-canvas-border text-secondary text-sm overflow-auto max-h-96">
              {JSON.stringify(plan.audit_plan_content, null, 2)}
            </pre>
          ) : (
            <p className="text-secondary italic">Audit plan content is being generated...</p>
          )}
          <div className="flex gap-3">
            <button className="btn-primary px-6 py-2" onClick={() => approvePlan.mutate()}
              disabled={approvePlan.isPending}>
              {approvePlan.isPending ? 'Approving...' : 'Approve Audit Plan'}
            </button>
          </div>
        </div>
      )}

      {/* Phase 5 — Request List */}
      {plan?.current_phase === 'request_list' && (
        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-display font-semibold text-primary">Phase 5 — Request List</h2>
          <p className="text-secondary text-sm">Due diligence request list. Update status and priority as documents are received.</p>
          {requestItems?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-canvas-border text-left">
                    <th className="p-3 text-secondary font-medium">#</th>
                    <th className="p-3 text-secondary font-medium">Workstream</th>
                    <th className="p-3 text-secondary font-medium">Audit Field</th>
                    <th className="p-3 text-secondary font-medium">Question</th>
                    <th className="p-3 text-secondary font-medium">Status</th>
                    <th className="p-3 text-secondary font-medium">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {requestItems.map(item => (
                    <tr key={item.id} className="border-b border-canvas-border/50 hover:bg-surface/50">
                      <td className="p-3 text-primary">{item.item_number}</td>
                      <td className="p-3 text-primary">{item.workstream}</td>
                      <td className="p-3 text-primary">{item.audit_field}</td>
                      <td className="p-3 text-primary max-w-xs truncate">{item.question}</td>
                      <td className="p-3">
                        <select className="input text-xs py-1 px-2" value={item.status}
                          onChange={e => updateItem.mutate({ itemId: item.id, data: { status: e.target.value as any } })}>
                          <option value="open">Open</option>
                          <option value="partial">Partial</option>
                          <option value="query">Query</option>
                          <option value="completed">Completed</option>
                        </select>
                      </td>
                      <td className="p-3">
                        <select className="input text-xs py-1 px-2" value={item.priority}
                          onChange={e => updateItem.mutate({ itemId: item.id, data: { priority: e.target.value as any } })}>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-secondary italic">No request items generated yet.</p>
          )}
        </div>
      )}

      {/* Basic Data Summary (always shown if plan exists) */}
      {plan?.basic_data && plan.current_phase !== 'basic_data' && (
        <div className="card p-6">
          <h3 className="text-sm font-display font-semibold text-secondary mb-3">Company Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-secondary">Company:</span> <span className="text-primary ml-1">{plan.basic_data.company_name}</span></div>
            <div><span className="text-secondary">Legal Form:</span> <span className="text-primary ml-1">{plan.basic_data.legal_form}</span></div>
            <div><span className="text-secondary">Industry:</span> <span className="text-primary ml-1">{plan.basic_data.industry}</span></div>
            <div><span className="text-secondary">Deal Type:</span> <span className="text-primary ml-1">{plan.basic_data.deal_type}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
