import { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { useProjectContext } from '../context/ProjectContext';
import { conversationsApi } from '../services/conversationsApi';
import { agentRunsApi, TERMINAL_RUN_STATUSES } from '../services/agentRunsApi';
import { modelsApi } from '../services/modelsApi';
import { documentsApi } from '../services/documentsApi';
import { deliverablesApi } from '../services/deliverablesApi';
import { approvalsApi } from '../services/approvalsApi';
import { toolsApi } from '../services/toolsApi';
import { api } from '../services/api';
import { AgentRun, Approval, ChatMessage, Deliverable, Document, Model, Routing } from '../services/types';
import { statusLabel } from '../components/common/StatusBadge';

type ExecutionStatus = 'done' | 'running' | 'pending' | 'waiting' | 'failed';

interface UI_Message extends ChatMessage {
  timestamp?: string;
}

interface RunView {
  run?: AgentRun;
  connectionLost?: boolean;
  deliverable?: Deliverable;
  approval?: Approval;
}

const MAX_CONSECUTIVE_POLL_ERRORS = 5;
const AGENTIC_TRIGGER = /analyze|inspect|report|approval|generate|prepare|extract/i;

const isTerminal = (run?: AgentRun) => !!run && TERMINAL_RUN_STATUSES.includes(run.status);

function errorText(err: any): string {
  if (err instanceof TypeError) return 'Backend unavailable — connection lost.';
  const detail = err?.data?.detail;
  return detail?.error?.message || detail?.message || err?.message || 'Unknown error';
}

function stepView(step: any, run: AgentRun, connectionLost?: boolean): { label: string; desc: string; status: ExecutionStatus } {
  const obs = [...(run.observations || [])].reverse().find(o => o.step_id === step.step_id);
  const duration = obs ? ` in ${(obs.duration_ms / 1000).toFixed(1)}s` : '';
  const label = step.description || step.capability || 'Step';
  if (step.status === 'completed') return { label, desc: `Completed${duration}`, status: 'done' };
  if (step.status === 'failed') return { label, desc: step.error?.message || 'Failed', status: 'failed' };
  if (connectionLost) return { label, desc: 'Lost connection to backend; run status unknown.', status: 'failed' };
  if (step.status === 'running') {
    return { label, desc: run.cancel_requested ? 'Cancellation requested — finishing current model call…' : 'Processing...', status: 'running' };
  }
  if (isTerminal(run)) return { label, desc: 'Not executed', status: 'pending' };
  return { label, desc: step.depends_on?.length ? `Waiting for ${step.depends_on.join(', ')}` : 'Queued', status: 'pending' };
}

export function ChatBench() {
  const { activeProject } = useProjectContext();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const requestedConversation = searchParams.get('conversation');

  const [messages, setMessages] = useState<UI_Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [defaultModel, setDefaultModel] = useState<Model | null>(null);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [toolCount, setToolCount] = useState<number | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<string>('unknown');
  const [runs, setRuns] = useState<Record<string, RunView>>({});
  const [attached, setAttached] = useState<Document | null>(null);
  const [attaching, setAttaching] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const sendingRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const stopAllPolling = () => {
    Object.values(pollingRef.current).forEach(clearTimeout);
    pollingRef.current = {};
  };

  const updateRun = (taskId: string, patch: Partial<RunView>) =>
    setRuns(prev => ({ ...prev, [taskId]: { ...prev[taskId], ...patch } }));

  function trackRun(taskId: string) {
    if (!activeProject || pollingRef.current[taskId]) return;
    const projectId = activeProject.project_id;
    let errors = 0;

    const poll = async () => {
      try {
        const run = await agentRunsApi.get(projectId, taskId);
        errors = 0;
        updateRun(taskId, { run, connectionLost: false });
        if (!isTerminal(run)) {
          pollingRef.current[taskId] = setTimeout(poll, 1500);
          return;
        }
        delete pollingRef.current[taskId];
        if (run.deliverable_id) {
          const [deliverable, approval] = await Promise.all([
            deliverablesApi.getMetadata(projectId, run.deliverable_id),
            run.approval_id ? approvalsApi.get(projectId, run.approval_id) : Promise.resolve(undefined),
          ]);
          updateRun(taskId, { deliverable, approval });
        }
      } catch (err) {
        errors += 1;
        if (errors < MAX_CONSECUTIVE_POLL_ERRORS) {
          pollingRef.current[taskId] = setTimeout(poll, 3000);
          return;
        }
        delete pollingRef.current[taskId];
        updateRun(taskId, { connectionLost: true });
      }
    };
    pollingRef.current[taskId] = setTimeout(poll, 0);
  }

  const loadConversation = async () => {
    if (!activeProject) return;
    setLoading(true);
    setLoadError(null);
    try {
      const history = await conversationsApi.getHistory(activeProject.project_id);
      history.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
      const conv = (requestedConversation && history.find(c => c.conversation_id === requestedConversation)) || history[0];
      setConversationId(conv?.conversation_id ?? null);
      const msgs = conv?.messages || [];
      setMessages(msgs);
      msgs.filter(m => m.execution_mode === 'agent' && m.task_id).forEach(m => trackRun(m.task_id!));
    } catch (err) {
      setLoadError(`Could not load conversation: ${errorText(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    stopAllPolling();
    setRuns({});
    setMessages([]);
    setConversationId(null);
    setAttached(null);
    if (!activeProject) {
      setDocuments([]);
      return;
    }
    loadConversation();

    setModelsLoaded(false);
    modelsApi.list().then(models => {
      setDefaultModel(models.find(m => m.role === 'general' && m.installed) || null);
    }).catch(err => setLoadError(`Could not load models: ${errorText(err)}`))
      .finally(() => setModelsLoaded(true));

    documentsApi.list(activeProject.project_id).then(docs => setDocuments(docs || []))
      .catch(err => setLoadError(`Could not load documents: ${errorText(err)}`));
    toolsApi.list().then(tools => setToolCount(tools.filter(t => t.available).length)).catch(() => setToolCount(null));
    api.get('/system/status').then(s => setOllamaStatus(s.ollama)).catch(() => setOllamaStatus('backend unavailable'));

    return stopAllPolling;
  }, [activeProject?.project_id, requestedConversation]);

  const agentMessages = messages.filter(m => m.execution_mode === 'agent' && m.task_id);
  const activeTaskId = agentMessages.map(m => m.task_id!).find(id => {
    const view = runs[id];
    return view?.run && !isTerminal(view.run) && !view.connectionLost;
  }) || null;
  const lastRouting: Routing | null | undefined = [...messages].reverse().find(m => m.routing)?.routing;
  const busy = loading || !!activeTaskId;

  async function sendMessage() {
    if (!activeProject || !input.trim() || sendingRef.current || activeTaskId) return;
    
    sendingRef.current = true;
    setLoading(true);
    
    const currentInput = input.trim();
    const isAgentic = AGENTIC_TRIGGER.test(currentInput) || !!attached;
    const userMsg: UI_Message = {
      message_id: 'temp-' + Date.now().toString(),
      role: 'user',
      content: currentInput,
      created_at: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      let currentConvId = conversationId;
      if (!currentConvId) {
        const conv = await conversationsApi.create(activeProject.project_id, { title: 'New Conversation' });
        currentConvId = conv.conversation_id;
        setConversationId(currentConvId);
      }

      const responseMsg = await conversationsApi.sendMessage(
        activeProject.project_id, 
        currentConvId, 
        { message: userMsg.content, mode: isAgentic ? 'agent' : 'chat', document_ids: attached ? [attached.document_id] : [] }
      );
      setAttached(null);
      setMessages(prev => [...prev, responseMsg]);

      if (responseMsg.execution_mode === 'agent' && responseMsg.task_id) {
        setExpandedSteps(prev => new Set(prev).add(responseMsg.message_id!));
        trackRun(responseMsg.task_id);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        message_id: 'err-' + Date.now().toString(),
        role: 'system',
        content: `Error: ${errorText(err)}`,
        status: 'failed',
        created_at: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      sendingRef.current = false;
    }
  }

  async function cancelActiveRun() {
    if (!activeProject || !activeTaskId) return;
    setCancelling(true);
    try {
      const run = await agentRunsApi.cancel(activeProject.project_id, activeTaskId);
      updateRun(activeTaskId, { run });
    } catch (err) {
      setLoadError(`Cancel failed: ${errorText(err)}`);
    } finally {
      setCancelling(false);
    }
  }

  async function handleAttach(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !activeProject) return;
    setAttaching(true);
    try {
      const result: any = await documentsApi.upload(activeProject.project_id, file);
      if (result?.error) throw new Error(result.error.message || result.error.code);
      const docs = await documentsApi.list(activeProject.project_id);
      setDocuments(docs);
      setAttached(docs.find(d => d.document_id === result.document_id) || null);
    } catch (err) {
      setLoadError(`Attachment upload failed: ${errorText(err)}`);
    } finally {
      setAttaching(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  const timeOf = (m: UI_Message) => new Date(m.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  const badgeModel = lastRouting ? `${lastRouting.model} · ${lastRouting.purpose}`
    : defaultModel ? `${defaultModel.name} · default`
    : modelsLoaded ? 'No model available' : 'Loading models…';

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Main chat area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header */}
        <div style={{
          padding: '12px 20px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0,
        }}>
          <div>
            <div className="font-display" style={{ fontSize: 15, fontWeight: 700 }}>ChatBench</div>
            <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>
              Project: {activeProject?.name || 'No Project Selected'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {conversationId && (
              <button onClick={() => { stopAllPolling(); setConversationId(null); setMessages([]); setRuns({}); navigate('/workbench'); }}
                className="btn-ghost" style={{ padding: '5px 10px', fontSize: 12 }} disabled={busy}>
                New chat
              </button>
            )}
            <span className="badge badge-violet" title={lastRouting ? `Router: ${lastRouting.reason}` : 'Configured general model (router picks per request)'}>{badgeModel}</span>
            <button
              onClick={() => setRightPanelOpen(v => !v)}
              className="btn-ghost"
              style={{ padding: '5px 10px', fontSize: 12 }}
            >
              Context
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </div>

        {loadError && (
          <div style={{ margin: '10px 20px 0', padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
            {loadError}
            <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={() => { setLoadError(null); loadConversation(); }}>Retry</button>
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
          <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
            {!activeProject && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5, textAlign: 'center' }}>Select a project to start.</p>}
            {messages.map(msg => {
              const isAgentic = msg.execution_mode === 'agent';
              const view = msg.task_id ? runs[msg.task_id] : undefined;
              const run = view?.run;
              const steps = run ? (run.plan?.steps || []).map(s => stepView(s, run, view?.connectionLost)) : [];
              const sources: any[] = (run?.plan?.steps.find(s => s.capability === 'knowledge_search' && s.result)?.result?.sources) || [];
              const answer: string | undefined = run?.final_result?.answer;
              const routing = run?.routing || msg.routing;
              return (
              <div key={msg.message_id}>
                {msg.role === 'user' ? (
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <div style={{
                      maxWidth: '70%',
                      background: 'var(--violet-dim)',
                      border: '1px solid rgba(124,58,237,0.25)',
                      borderRadius: '12px 12px 4px 12px',
                      padding: '12px 16px',
                    }}>
                      <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: 'var(--foreground)' }}>{msg.content}</p>
                      <div style={{ fontSize: 10.5, color: 'rgba(167,139,250,0.6)', marginTop: 6, textAlign: 'right', fontFamily: 'JetBrains Mono' }}>{timeOf(msg)}</div>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{
                      width: 30, height: 30, borderRadius: 8, flexShrink: 0,
                      background: 'linear-gradient(135deg, #7C3AED, #0F766E)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6, flexWrap: 'wrap' }}>
                        <span className="font-display" style={{ fontSize: 13, fontWeight: 700 }}>Builder AI</span>
                        <span style={{ fontSize: 10.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{timeOf(msg)}</span>
                        {isAgentic && <span className="badge badge-amber">Agentic</span>}
                        {routing && <span className="badge badge-gray" title={routing.reason}>{routing.model}</span>}
                        {run && <span className={`badge ${run.status === 'completed' ? 'badge-green' : run.status === 'failed' ? 'badge-red' : run.status === 'cancelled' ? 'badge-gray' : 'badge-violet'}`}>{statusLabel(run.status)}</span>}
                        {msg.status === 'failed' && !run && <span className="badge badge-red">Failed</span>}
                      </div>

                      <div style={{
                        background: 'var(--surface-1)', border: `1px solid ${msg.status === 'failed' && !run ? 'rgba(239,68,68,0.35)' : 'var(--border)'}`,
                        borderRadius: '4px 12px 12px 12px', padding: '12px 16px',
                      }}>
                        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.65, color: 'var(--foreground)', whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                        {isAgentic && !run && !view?.connectionLost && <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--muted-foreground)' }}>Loading run state…</p>}
                        {view?.connectionLost && <p style={{ margin: '8px 0 0', fontSize: 12, color: '#F87171' }}>Backend unavailable — connection lost while tracking this run.</p>}
                        {run?.error && (
                          <p style={{ margin: '8px 0 0', fontSize: 12.5, color: run.status === 'cancelled' ? 'var(--muted-foreground)' : '#F87171' }}>
                            {run.error.code}: {run.error.message}
                          </p>
                        )}
                        {answer && <p style={{ margin: '10px 0 0', fontSize: 13.5, lineHeight: 1.6, color: 'var(--foreground)', whiteSpace: 'pre-wrap' }}>{answer}</p>}
                        {sources.length > 0 && (
                          <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                            <span style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>Sources:</span>
                            {Array.from(new Map(sources.map(s => [`${s.filename}|${s.page_number}`, s])).values()).map((s, i) => (
                              <span key={i} className="badge badge-gray" style={{ fontSize: 10.5 }}>{s.filename}{s.page_number ? ` p.${s.page_number}` : ''}</span>
                            ))}
                          </div>
                        )}

                        {/* Agent execution steps */}
                        {isAgentic && run && (
                          <div style={{ marginTop: 14 }}>
                            <button
                              onClick={() => setExpandedSteps(prev => {
                                const next = new Set(prev);
                                if (next.has(msg.message_id!)) next.delete(msg.message_id!);
                                else next.add(msg.message_id!);
                                return next;
                              })}
                              className="btn-ghost"
                              style={{ padding: '4px 8px', fontSize: 12, marginBottom: 8 }}
                            >
                              {expandedSteps.has(msg.message_id!) ? '▼' : '▶'} Execution Timeline ({steps.filter(s => s.status === 'done').length}/{steps.length} steps{run.replan_count ? `, ${run.replan_count} replans` : ''})
                            </button>
                            {expandedSteps.has(msg.message_id!) && (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingLeft: 8 }}>
                                {steps.length === 0 && <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>Planning…</div>}
                                {steps.map((step, si) => (
                                  <div key={si} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                                    <StepDot status={step.status} />
                                    <div>
                                      <div style={{ fontSize: 12.5, fontWeight: 600, color: step.status === 'running' ? '#A78BFA' : 'var(--foreground)' }}>
                                        {step.label}
                                        {step.status === 'running' && <span className="animate-pulse-soft" style={{ marginLeft: 6 }}>•••</span>}
                                      </div>
                                      <div style={{ fontSize: 11.5, color: step.status === 'failed' ? '#F87171' : 'var(--muted-foreground)' }}>{step.desc}</div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Result card */}
                        {view?.deliverable && activeProject && (
                          <div style={{
                            marginTop: 16,
                            background: 'var(--surface-2)', border: '1px solid rgba(16,185,129,0.2)',
                            borderRadius: 10, padding: '14px 16px',
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#10B981" strokeWidth="1.5"/><polyline points="14 2 14 8 20 8" stroke="#10B981" strokeWidth="1.5"/></svg>
                              <span className="font-display" style={{ fontSize: 14, fontWeight: 700, color: 'var(--foreground)', wordBreak: 'break-all' }}>{view.deliverable.filename}</span>
                            </div>
                            {view.approval && (
                              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14 }}>
                                <span className="badge badge-amber">{statusLabel(view.approval.status)}</span>
                              </div>
                            )}
                            <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)', marginBottom: 12, fontStyle: 'italic' }}>
                              AI-generated draft — Human review required before finalizing.
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                              <a className="btn-primary" style={{ fontSize: 12.5, padding: '7px 16px' }} href={deliverablesApi.getDownloadUrl(activeProject.project_id, view.deliverable.deliverable_id)}>
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                                Download Approval Note ({view.deliverable.type})
                              </a>
                              <button className="btn-secondary" style={{ fontSize: 12.5, padding: '7px 14px' }} onClick={() => navigate(`/workbench/runs?run=${msg.task_id}`)}>View Details</button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              );
            })}
            {loading && (
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, background: 'linear-gradient(135deg, #7C3AED, #0F766E)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </div>
                <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: '4px 12px 12px 12px', padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{
                        width: 6, height: 6, borderRadius: '50%', background: '#7C3AED',
                        animation: `pulse-soft 1.2s ease-in-out ${i * 0.2}s infinite`,
                      }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', flexShrink: 0, background: 'var(--surface-1)' }}>
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            {(activeTaskId || attached || attaching) && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                {activeTaskId && (
                  <>
                    <span className="badge badge-violet" style={{ fontSize: 11 }}>
                      {runs[activeTaskId]?.run?.cancel_requested ? 'CANCELLING…' : `PROCESSING · ${statusLabel(runs[activeTaskId]?.run?.status || 'queued')}`}
                    </span>
                    <button className="btn-secondary" style={{ fontSize: 12, padding: '4px 12px', color: '#EF4444' }}
                      onClick={cancelActiveRun} disabled={cancelling || !!runs[activeTaskId]?.run?.cancel_requested}>
                      Cancel task
                    </button>
                  </>
                )}
                {attaching && <span className="badge badge-gray" style={{ fontSize: 11 }}>Uploading attachment…</span>}
                {attached && (
                  <span className="badge badge-teal" style={{ fontSize: 11 }}>
                    📎 {attached.original_filename}
                    <button className="btn-ghost" style={{ padding: '0 4px', marginLeft: 4, fontSize: 11 }} onClick={() => setAttached(null)}>×</button>
                  </span>
                )}
              </div>
            )}
            <div style={{
              background: 'var(--surface-2)', border: '1px solid var(--border)',
              borderRadius: 12, display: 'flex', alignItems: 'flex-end', gap: 10, padding: '10px 14px',
              transition: 'border-color 0.2s',
            }}>
              <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleAttach}
                accept=".pdf,.docx,.txt,.xlsx,.csv,.png,.jpg,.jpeg,.webp" />
              <button className="btn-ghost" style={{ padding: '4px 6px', flexShrink: 0 }} title="Attach file"
                onClick={() => fileInputRef.current?.click()} disabled={!activeProject || attaching || busy}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
              </button>
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
                }}
                disabled={!activeProject || !!activeTaskId}
                placeholder={activeTaskId ? 'Tuffy is processing — cancel the task or wait for it to finish…' : 'Message Builder AI — try "Analyze this inspection report" or just ask anything...'}
                rows={1}
                style={{
                  flex: 1, background: 'transparent', border: 'none', outline: 'none',
                  color: 'var(--foreground)', fontSize: 14, resize: 'none',
                  fontFamily: 'Inter, sans-serif', lineHeight: 1.5, maxHeight: 120,
                }}
                onInput={e => {
                  const el = e.currentTarget;
                  el.style.height = 'auto';
                  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || busy}
                title={busy ? 'Processing' : 'Send'}
                style={{
                  width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                  background: input.trim() && !busy ? 'var(--primary)' : 'var(--surface-3)',
                  border: 'none', cursor: input.trim() && !busy ? 'pointer' : 'default',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.2s',
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
              </button>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
              {['Analyze inspection report', 'Summarize findings', 'Prepare approval note'].map(s => (
                <button key={s} onClick={() => setInput(s)} className="btn-ghost" disabled={!!activeTaskId}
                  style={{ fontSize: 11.5, padding: '4px 10px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6 }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right context panel */}
      {rightPanelOpen && (
        <div style={{
          width: 260, borderLeft: '1px solid var(--border)',
          background: 'var(--surface-1)', padding: '16px',
          overflowY: 'auto', flexShrink: 0,
        }} className="chat-right-panel">
          <div className="font-display" style={{ fontSize: 13, fontWeight: 700, marginBottom: 14 }}>Context</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'Model', value: lastRouting?.model || defaultModel?.name || '—' },
              { label: 'Routing', value: lastRouting ? lastRouting.purpose : 'default' },
              { label: 'Project', value: activeProject?.name || 'None' },
              { label: 'Documents', value: `${documents.length} available` },
              { label: 'Tools', value: toolCount === null ? 'unavailable' : `${toolCount} registered` },
              { label: 'Ollama', value: ollamaStatus },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 7, border: '1px solid var(--border)' }}>
                <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{item.label}</span>
                <span style={{ fontSize: 12, fontWeight: 600, fontFamily: 'JetBrains Mono', color: 'var(--foreground)', textAlign: 'right', wordBreak: 'break-all' }}>{item.value}</span>
              </div>
            ))}
            {lastRouting && <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>Router: {lastRouting.reason}</div>}
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="section-label" style={{ marginBottom: 10 }}>Active Sources</div>
            {documents.length > 0 ? documents.map(doc => (
              <div key={doc.document_id} style={{ padding: '7px 10px', borderRadius: 6, background: 'var(--surface-2)', marginBottom: 4, fontSize: 11.5, color: 'var(--muted-foreground)', display: 'flex', gap: 6, alignItems: 'center' }}>
                <span>📄</span> {doc.original_filename || doc.filename || 'Untitled Document'}
              </div>
            )) : (
              <div style={{ fontSize: 12, color: 'var(--muted-foreground)', fontStyle: 'italic' }}>No documents in project</div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @media (max-width: 900px) { .chat-right-panel { display: none; } }
      `}</style>
    </div>
  );
}

function StepDot({ status }: { status: ExecutionStatus }) {
  const cls = {
    done: 'step-dot-done',
    running: 'step-dot-running',
    pending: 'step-dot-pending',
    waiting: 'step-dot-waiting',
    failed: 'step-dot-waiting',
  }[status];
  const icon = {
    done: '✓',
    running: '•',
    pending: '○',
    waiting: '!',
    failed: '✕',
  }[status];
  return <div className={`step-dot ${cls}`}>{icon}</div>;
}
