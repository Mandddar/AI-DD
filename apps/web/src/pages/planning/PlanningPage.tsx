import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { planning, type BasicDataInput, type RequestItem } from '../../api/planning';
import { usePermissions } from '../../hooks/usePermissions';
import {
  ClipboardList, Building2, AlertTriangle, MessageSquare,
  CheckCircle2, FileSpreadsheet, ChevronRight, Loader2, Send, X,
  User, Check, Clock, MessageCircle,
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
  const perms = usePermissions();

  const { data: plan, isLoading } = useQuery({
    queryKey: ['planning', projectId],
    queryFn: () => planning.getPlan(projectId!).catch((err) => {
      if (err.response?.status === 404) return null;
      throw err;
    }),
    retry: false,
  });

  const { data: requestItems } = useQuery({
    queryKey: ['requestList', projectId],
    queryFn: () => planning.getRequestList(projectId!),
    enabled: plan?.current_phase === 'request_list',
  });

  const { data: teamMembers } = useQuery({
    queryKey: ['team-members', projectId],
    queryFn: () => planning.getTeamMembers(projectId!),
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

  const [queryDialog, setQueryDialog] = useState<{ itemId: string; question: string } | null>(null);
  const [queryText, setQueryText] = useState('');
  const [dialogAnswers, setDialogAnswers] = useState<Record<number, string>>({});
  const [chatItemId, setChatItemId] = useState<string | null>(null);
  const [chatMsg, setChatMsg] = useState('');

  const { data: chatMessages, refetch: refetchChat } = useQuery({
    queryKey: ['planning-chat', projectId, chatItemId],
    queryFn: () => planning.getChatMessages(projectId!, chatItemId || undefined),
    enabled: !!chatItemId,
    refetchInterval: chatItemId ? 5000 : false,
  });

  const sendChat = useMutation({
    mutationFn: () => planning.sendChatMessage(projectId!, chatMsg, chatItemId || undefined),
    onSuccess: () => { setChatMsg(''); refetchChat(); },
  });

  const answerQuestion = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: number; answer: string }) =>
      planning.answerDialogQuestion(projectId!, questionId, answer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['planning', projectId] });
    },
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
        <ClipboardList className="w-8 h-8 text-gold" />
        <h1 className="text-3xl font-display font-bold text-primary">Audit Planning</h1>
      </div>

      {/* Phase Stepper */}
      <div className="card p-7">
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
                  <span className="text-base font-medium hidden lg:inline">{phase.label}</span>
                </div>
                {idx < PHASES.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-secondary/40 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* No Plan Yet - Show Phase 1 Form (advisors only) or read-only message */}
      {!plan && perms.canManagePlanning && (
        <div className="card p-7 space-y-6">
          <h2 className="text-xl font-display font-semibold text-primary">Phase 1 - Basic Company Data</h2>
          <p className="text-secondary text-base">Enter the target company's basic information to begin the audit planning process.</p>
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
      {!plan && !perms.canManagePlanning && (
        <div className="card p-7 text-center">
          <ClipboardList className="w-14 h-14 text-secondary/30 mx-auto mb-3" />
          <p className="text-secondary">No audit plan has been created yet.</p>
          <p className="text-secondary/60 text-base mt-1">An advisor will set up the planning process.</p>
        </div>
      )}

      {/* Phase 1 complete but stuck (legacy plans) - show advance button */}
      {plan?.current_phase === 'basic_data' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary">Phase 1 - Basic Data Submitted</h2>
          <p className="text-secondary text-base">Company data has been recorded. Advance to AI Risk Analysis.</p>
          {perms.canManagePlanning && (
            <button className="btn-primary px-6 py-2" onClick={() => advancePhase.mutate()}
              disabled={advancePhase.isPending}>
              {advancePhase.isPending ? 'Generating Risk Analysis...' : 'Proceed to Risk Analysis'}
            </button>
          )}
        </div>
      )}

      {/* Phase 2 - Risk Analysis */}
      {plan?.current_phase === 'risk_analysis' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary">Phase 2 - AI Risk Analysis</h2>
          <p className="text-secondary text-base">AI-derived risk areas based on company profile.</p>
          {plan.risk_analysis?.length ? (
            <div className="space-y-3">
              {plan.risk_analysis.map((risk: any, i: number) => (
                <div key={i} className="bg-surface p-4 rounded-lg border border-canvas-border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-primary">{risk.risk_area || risk.title}</span>
                    <span className={`text-sm px-2 py-1 rounded-full ${
                      risk.severity === 'high' ? 'bg-risk-high/10 text-risk-high' :
                      risk.severity === 'medium' ? 'bg-risk-medium/10 text-risk-medium' :
                      'bg-risk-low/10 text-risk-low'
                    }`}>{risk.severity}</span>
                  </div>
                  <p className="text-secondary text-base">{risk.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary italic">Risk analysis is being generated...</p>
          )}
          {perms.canManagePlanning && (
            <button className="btn-primary px-6 py-2" onClick={() => advancePhase.mutate()}
              disabled={advancePhase.isPending}>
              {advancePhase.isPending ? 'Processing...' : 'Proceed to Interactive Dialog'}
            </button>
          )}
        </div>
      )}

      {/* Phase 3 - Interactive Dialog */}
      {plan?.current_phase === 'dialog' && (
        <div className="card p-7 space-y-5">
          <div>
            <h2 className="text-xl font-display font-semibold text-primary">Phase 3 - Interactive Dialog</h2>
            <p className="text-secondary text-base mt-1">
              {perms.isReadOnly
                ? "Review the questions and answers below."
                : "Answer the AI-generated follow-up questions below. All team members can contribute answers."}
            </p>
          </div>

          {plan.dialog_history?.length ? (
            <div className="space-y-4">
              {plan.dialog_history.map((item: { question: string; answer?: string; answered_by_name?: string; answered_by_role?: string }, i: number) => {
                const hasAnswer = !!item.answer;
                const draftAnswer = dialogAnswers[i] ?? '';
                const canAnswer = perms.canUpdateRequestList && !perms.isReadOnly;

                return (
                  <div key={i} className={`rounded-xl border transition-all ${
                    hasAnswer ? 'border-risk-low/30 bg-risk-low/5' : 'border-canvas-border bg-surface/50'
                  }`}>
                    {/* Question */}
                    <div className="flex items-start gap-3 p-5 pb-3">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gold/10 text-gold text-xs font-bold mt-0.5">
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-base font-medium text-text-primary leading-relaxed">{item.question}</p>
                      </div>
                      {hasAnswer ? (
                        <span className="shrink-0 flex items-center gap-1 text-xs text-risk-low bg-risk-low/10 rounded-full px-2.5 py-1">
                          <Check size={12} /> Answered
                        </span>
                      ) : (
                        <span className="shrink-0 flex items-center gap-1 text-xs text-text-muted bg-surface rounded-full px-2.5 py-1">
                          <Clock size={12} /> Pending
                        </span>
                      )}
                    </div>

                    {/* Answer display or input */}
                    <div className="px-5 pb-5 pl-15">
                      {hasAnswer ? (
                        <div>
                          <div className="bg-canvas-card border border-canvas-border rounded-lg p-4">
                            <p className="text-base text-text-primary leading-relaxed">{item.answer}</p>
                          </div>
                          {item.answered_by_name && (
                            <div className="flex items-center gap-2 mt-2 text-xs text-text-muted">
                              <User size={12} />
                              <span>{item.answered_by_name}</span>
                              {item.answered_by_role && (
                                <span className="text-text-muted/60">({item.answered_by_role.replace('_', ' ')})</span>
                              )}
                            </div>
                          )}
                          {/* Allow re-answering for advisors */}
                          {perms.canManagePlanning && !dialogAnswers.hasOwnProperty(i) && (
                            <button
                              className="text-xs text-gold hover:text-gold-light mt-2 transition-colors"
                              onClick={() => setDialogAnswers(prev => ({ ...prev, [i]: item.answer || '' }))}
                            >
                              Edit answer
                            </button>
                          )}
                          {dialogAnswers.hasOwnProperty(i) && (
                            <div className="mt-3 space-y-2">
                              <textarea
                                className="input w-full h-24 resize-none"
                                value={draftAnswer}
                                onChange={e => setDialogAnswers(prev => ({ ...prev, [i]: e.target.value }))}
                                placeholder="Update your answer..."
                              />
                              <div className="flex gap-2">
                                <button
                                  className="btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5"
                                  disabled={!draftAnswer.trim() || answerQuestion.isPending}
                                  onClick={() => {
                                    answerQuestion.mutate({ questionId: i, answer: draftAnswer.trim() }, {
                                      onSuccess: () => setDialogAnswers(prev => { const n = { ...prev }; delete n[i]; return n; }),
                                    });
                                  }}
                                >
                                  <Send size={13} /> Update
                                </button>
                                <button
                                  className="btn-ghost text-sm px-4 py-1.5"
                                  onClick={() => setDialogAnswers(prev => { const n = { ...prev }; delete n[i]; return n; })}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : canAnswer ? (
                        <div className="space-y-2">
                          <textarea
                            className="input w-full h-24 resize-none"
                            value={draftAnswer}
                            onChange={e => setDialogAnswers(prev => ({ ...prev, [i]: e.target.value }))}
                            placeholder={
                              perms.isAdvisor
                                ? "Provide your assessment or information..."
                                : "Provide the requested information or document reference..."
                            }
                          />
                          <button
                            className="btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5"
                            disabled={!draftAnswer.trim() || answerQuestion.isPending}
                            onClick={() => {
                              answerQuestion.mutate({ questionId: i, answer: draftAnswer.trim() }, {
                                onSuccess: () => setDialogAnswers(prev => { const n = { ...prev }; delete n[i]; return n; }),
                              });
                            }}
                          >
                            {answerQuestion.isPending ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                            Submit Answer
                          </button>
                        </div>
                      ) : (
                        <p className="text-sm text-text-muted italic">Awaiting response from the team.</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <MessageSquare className="w-14 h-14 text-text-muted/20 mx-auto mb-3" />
              <p className="text-secondary">No dialog questions generated yet.</p>
            </div>
          )}

          {/* Progress + Advance button */}
          {plan.dialog_history?.length ? (
            <div className="flex items-center justify-between pt-2 border-t border-canvas-border">
              <div className="text-sm text-text-secondary">
                {plan.dialog_history.filter((q: { answer?: string }) => q.answer).length} of {plan.dialog_history.length} questions answered
              </div>
              {perms.canManagePlanning && (
                <button className="btn-primary px-6 py-2" onClick={() => advancePhase.mutate()}
                  disabled={advancePhase.isPending}>
                  {advancePhase.isPending ? 'Processing...' : 'Proceed to Plan Approval'}
                </button>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Phase 4 - Audit Plan Approval */}
      {plan?.current_phase === 'plan_approval' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary">Phase 4 - Audit Plan Approval</h2>
          <p className="text-secondary text-base">Review the generated audit plan. Specialized agents will only begin work after your approval.</p>
          {plan.audit_plan_content ? (
            <pre className="bg-surface p-4 rounded-lg border border-canvas-border text-secondary text-base overflow-auto max-h-96">
              {JSON.stringify(plan.audit_plan_content, null, 2)}
            </pre>
          ) : (
            <p className="text-secondary italic">Audit plan content is being generated...</p>
          )}
          {perms.canManagePlanning && (
            <div className="flex gap-3">
              <button className="btn-primary px-6 py-2" onClick={() => approvePlan.mutate()}
                disabled={approvePlan.isPending}>
                {approvePlan.isPending ? 'Approving...' : 'Approve Audit Plan'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Phase 5 - Request List */}
      {plan?.current_phase === 'request_list' && (
        <div className="card p-7 space-y-4">
          <h2 className="text-xl font-display font-semibold text-primary">Phase 5 - Request List</h2>
          <p className="text-secondary text-base">Due diligence request list. Update status and priority as documents are received.</p>
          {requestItems?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-base">
                <thead>
                  <tr className="border-b border-canvas-border text-left">
                    <th className="p-3 text-secondary font-medium">#</th>
                    <th className="p-3 text-secondary font-medium">Workstream</th>
                    <th className="p-3 text-secondary font-medium">Audit Field</th>
                    <th className="p-3 text-secondary font-medium">Question</th>
                    <th className="p-3 text-secondary font-medium">Assigned To</th>
                    <th className="p-3 text-secondary font-medium">Status</th>
                    <th className="p-3 text-secondary font-medium">Priority</th>
                    <th className="p-3 text-secondary font-medium">Chat</th>
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
                        <select className="input text-sm py-1 px-2" value={item.assigned_to || ''}
                          disabled={!perms.canManagePlanning}
                          onChange={e => updateItem.mutate({ itemId: item.id, data: { assigned_to: e.target.value || null } as any })}>
                          <option value="">Unassigned</option>
                          {teamMembers?.map(m => (
                            <option key={m.id} value={m.id}>{m.name || m.email}</option>
                          ))}
                        </select>
                      </td>
                      <td className="p-3">
                        <select className="input text-sm py-1 px-2" value={item.status}
                          disabled={!perms.canUpdateRequestList}
                          onChange={e => {
                            const val = e.target.value;
                            if (val === 'query') {
                              setQueryDialog({ itemId: item.id, question: item.question });
                              setQueryText('');
                            } else {
                              updateItem.mutate({ itemId: item.id, data: { status: val as any } });
                            }
                          }}>
                          <option value="open">Open</option>
                          <option value="partial">Partial</option>
                          <option value="query">Query</option>
                          <option value="completed">Completed</option>
                        </select>
                      </td>
                      <td className="p-3">
                        <select className="input text-sm py-1 px-2" value={item.priority}
                          disabled={!perms.canUpdateRequestList}
                          onChange={e => updateItem.mutate({ itemId: item.id, data: { priority: e.target.value as any } })}>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </td>
                      <td className="p-3">
                        <button
                          onClick={() => setChatItemId(chatItemId === item.id ? null : item.id)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            chatItemId === item.id ? 'bg-gold/10 text-gold' : 'text-text-muted hover:text-text-primary hover:bg-surface'
                          }`}
                          title="Open discussion"
                        >
                          <MessageCircle size={16} />
                        </button>
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

      {/* Chat Panel — shows below the request list when a chat is opened */}
      {chatItemId && (
        <div className="card overflow-hidden animate-fade-in">
          <div className="flex items-center justify-between p-5 border-b border-canvas-border">
            <div className="flex items-center gap-2">
              <MessageCircle size={18} className="text-gold" />
              <h3 className="text-base font-semibold text-text-primary">
                Discussion — Item #{requestItems?.find(i => i.id === chatItemId)?.item_number}
              </h3>
            </div>
            <button onClick={() => setChatItemId(null)} className="text-text-muted hover:text-text-primary transition-colors">
              <X size={18} />
            </button>
          </div>

          <div className="p-4 bg-canvas-subtle border-b border-canvas-border">
            <p className="text-sm text-text-secondary">
              {requestItems?.find(i => i.id === chatItemId)?.question}
            </p>
          </div>

          {/* Messages */}
          <div className="max-h-64 overflow-y-auto p-4 space-y-3">
            {chatMessages?.length ? (
              chatMessages.map((m: { id: string; sender_name: string; sender_role: string | null; message: string; created_at: string }) => (
                <div key={m.id} className="flex items-start gap-2.5">
                  <div className="h-7 w-7 shrink-0 rounded-full bg-surface flex items-center justify-center text-xs font-semibold text-text-secondary">
                    {m.sender_name?.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text-primary">{m.sender_name}</span>
                      {m.sender_role && <span className="text-xs text-text-muted capitalize">{m.sender_role.replace('_', ' ')}</span>}
                      <span className="text-xs text-text-muted">{new Date(m.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm text-text-secondary mt-0.5">{m.message}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No messages yet. Start the discussion.</p>
            )}
          </div>

          {/* Input */}
          {!perms.isReadOnly && (
            <div className="p-4 border-t border-canvas-border flex gap-2">
              <input
                className="input flex-1"
                placeholder="Type a message..."
                value={chatMsg}
                onChange={e => setChatMsg(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && chatMsg.trim()) sendChat.mutate(); }}
              />
              <button
                className="btn-primary px-4 py-2 flex items-center gap-1.5"
                disabled={!chatMsg.trim() || sendChat.isPending}
                onClick={() => sendChat.mutate()}
              >
                <Send size={14} /> Send
              </button>
            </div>
          )}
        </div>
      )}

      {/* Query Composition Dialog */}
      {queryDialog && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setQueryDialog(null)}>
          <div className="bg-canvas-card border border-canvas-border rounded-xl max-w-lg w-full overflow-hidden"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b border-canvas-border">
              <div>
                <h2 className="text-xl font-display font-semibold text-primary">Compose Query</h2>
                <p className="text-secondary text-sm mt-1">Send a query to the seller regarding this request item.</p>
              </div>
              <button onClick={() => setQueryDialog(null)} className="text-secondary hover:text-primary"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="label">Request Item</label>
                <p className="text-primary text-base bg-surface rounded-lg p-3 border border-canvas-border">{queryDialog.question}</p>
              </div>
              <div>
                <label className="label">Query Message</label>
                <textarea
                  className="input w-full h-32 resize-none"
                  placeholder="Describe what additional information or clarification you need from the seller..."
                  value={queryText}
                  onChange={e => setQueryText(e.target.value)}
                />
              </div>
            </div>
            <div className="p-4 border-t border-canvas-border flex justify-end gap-3">
              <button className="btn-ghost px-4 py-2 text-base" onClick={() => setQueryDialog(null)}>Cancel</button>
              <button
                className="btn-primary px-4 py-2 text-base flex items-center gap-2"
                disabled={!queryText.trim()}
                onClick={() => {
                  // Send as chat message + update status
                  planning.sendChatMessage(projectId!, queryText.trim(), queryDialog.itemId).then(() => {
                    updateItem.mutate(
                      { itemId: queryDialog.itemId, data: { status: 'query' as any } },
                      { onSuccess: () => { setQueryDialog(null); setQueryText(''); setChatItemId(queryDialog.itemId); } }
                    );
                  });
                }}
              >
                <Send className="w-4 h-4" /> Send Query
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Basic Data Summary (always shown if plan exists) */}
      {plan?.basic_data && plan.current_phase !== 'basic_data' && (
        <div className="card p-7">
          <h3 className="text-base font-display font-semibold text-secondary mb-3">Company Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-base">
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
