import { useEffect, useState } from 'react';
import { useProjectContext } from '../context/ProjectContext';
import { agentRunsApi, TERMINAL_RUN_STATUSES } from '../services/agentRunsApi';
import { AgentRun } from '../services/types';
import { StatusBadge, describeError } from '../components/common/StatusBadge';

type PhaseStatus = 'done' | 'running' | 'pending' | 'failed';

interface Phase {
  id: string;
  label: string;
  icon: string;
  color: string;
  status: PhaseStatus;
  desc: string;
}

function buildPhases(run: AgentRun): Phase[] {
  const steps = run.plan?.steps || [];
  const done = steps.filter(s => s.status === 'completed').length;
  const lastValidation = run.validation_results[run.validation_results.length - 1];
  const terminal = TERMINAL_RUN_STATUSES.includes(run.status);
  const failed = run.status === 'failed' || run.status === 'cancelled';
  return [
    {
      id: 'plan', label: 'PLAN', icon: '🧠', color: '#A78BFA',
      status: run.status === 'planning' ? 'running' : steps.length ? 'done' : failed ? 'failed' : 'pending',
      desc: steps.length ? `${steps.length} step(s) planned.${run.routing ? ` Routed to ${run.routing.model} — ${run.routing.reason}.` : ''}` : 'Waiting for plan.',
    },
    {
      id: 'execute', label: 'EXECUTE', icon: '⚙️', color: '#14B8A6',
      status: run.status === 'executing' ? 'running' : steps.some(s => s.status === 'failed') && terminal && failed ? 'failed' : done ? 'done' : 'pending',
      desc: `${done}/${steps.length} step(s) completed, ${run.step_count} execution(s) total.`,
    },
    {
      id: 'observe', label: 'OBSERVE', icon: '👁️', color: '#F59E0B',
      status: run.status === 'observing' ? 'running' : run.observations.length ? 'done' : 'pending',
      desc: `${run.observations.length} observation(s) recorded.`,
    },
    {
      id: 'validate', label: 'VALIDATE', icon: '✓', color: '#10B981',
      status: run.status === 'validating' ? 'running' : !lastValidation ? 'pending' : lastValidation.valid ? 'done' : 'failed',
      desc: lastValidation ? `Last: ${lastValidation.valid ? 'valid' : 'invalid'} — ${lastValidation.reason}` : 'No validation yet.',
    },
    {
      id: 'replan', label: 'REPLAN / DELIVER', icon: '📋', color: '#6D28D9',
      status: run.status === 'replanning' ? 'running' : run.status === 'completed' ? 'done' : failed ? 'failed' : 'pending',
      desc: `${run.replan_count}/${run.max_replans} replan(s). ${run.status === 'completed' ? (run.deliverable_id ? 'Deliverable issued for human sign-off.' : 'Completed.') : run.error ? `${run.error.code}: ${run.error.message}` : ''}`,
    },
  ];
}

export function Tuffy() {
  const { activeProject } = useProjectContext();
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['plan', 'execute']));
  const [logOpen, setLogOpen] = useState(false);

  useEffect(() => {
    if (!activeProject) { setRun(null); return; }
    let timer: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;
    const load = async () => {
      setError(null);
      try {
        const runs = await agentRunsApi.list(activeProject.project_id);
        const latest = runs.find(r => !TERMINAL_RUN_STATUSES.includes(r.status)) || runs[0] || null;
        if (stopped) return;
        setRun(latest);
        if (latest && !TERMINAL_RUN_STATUSES.includes(latest.status)) timer = setTimeout(load, 2000);
      } catch (err) {
        if (!stopped) setError(describeError(err, 'Tuffy runs'));
      } finally {
        if (!stopped) setLoading(false);
      }
    };
    setLoading(true);
    load();
    return () => { stopped = true; if (timer) clearTimeout(timer); };
  }, [activeProject]);

  function toggle(id: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function cancelRun() {
    if (!activeProject || !run) return;
    setCancelling(true);
    try {
      setRun(await agentRunsApi.cancel(activeProject.project_id, run.task_id));
    } catch (err) {
      setError(describeError(err, 'cancel').replace('Failed to load cancel', 'Cancel failed'));
    } finally {
      setCancelling(false);
    }
  }

  const phases = run ? buildPhases(run) : [];
  const steps = run?.plan?.steps || [];
  const active = steps.find(s => s.step_id === run?.current_step);
  const searchStep = steps.find(s => s.capability === 'knowledge_search' && s.result);
  const sources: any[] = searchStep?.result?.sources || [];
  const toolsUsed = Array.from(new Set(steps.map(s => s.input?.tool_name || s.capability)));
  const running = !!run && !TERMINAL_RUN_STATUSES.includes(run.status);
  const log = run ? [
    { time: run.created_at, level: 'info', msg: `Run created: ${run.task_id}` },
    ...run.observations.map(o => ({ time: o.timestamp, level: o.status === 'success' || o.status === 'completed' ? 'success' : 'warn', msg: `${o.step_id} (${o.capability}) ${o.status} in ${(o.duration_ms / 1000).toFixed(1)}s${o.summary ? ` — ${o.summary}` : ''}` })),
    ...run.validation_results.map(v => ({ time: '', level: v.valid ? 'success' : 'warn', msg: `validate ${v.step_id}: ${v.valid ? 'valid' : 'invalid'} — ${v.reason}` })),
    ...(run.completed_at ? [{ time: run.completed_at, level: run.status === 'completed' ? 'success' : 'warn', msg: `Run ${run.status}${run.error ? `: ${run.error.message}` : ''}` }] : []),
  ] : [];

  return (
    <div style={{ padding: '24px', display: 'flex', gap: 24, height: '100%', overflow: 'hidden', minHeight: 0, flexDirection: 'column' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Agentic Orchestrator</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Tuffy</h1>
            <p style={{ margin: '5px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
              Plan · Execute · Observe · Validate · Replan
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {run && <StatusBadge status={run.status} />}
            {running && (
              <button className="btn-secondary" style={{ fontSize: 12.5, color: '#EF4444' }} onClick={cancelRun} disabled={cancelling || run?.cancel_requested}>
                {run?.cancel_requested ? 'Cancelling…' : 'Cancel task'}
              </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>{error}</div>
      )}

      {!activeProject ? (
        <Empty text="Select a project to view Tuffy activity." />
      ) : loading && !run ? (
        <Empty text="Loading Tuffy runs…" />
      ) : !run ? (
        <Empty text="No Tuffy runs in this project yet. Send an agentic request from ChatBench." />
      ) : (
      <div style={{ flex: 1, display: 'flex', gap: 20, overflow: 'hidden', minHeight: 0 }}>
        {/* Workflow column */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {phases.map((step, i) => (
            <div key={step.id}>
              {/* Step card */}
              <div
                style={{
                  background: 'var(--surface-1)', border: `1px solid ${step.status === 'running' ? step.color + '50' : step.status === 'failed' ? 'rgba(239,68,68,0.35)' : 'var(--border)'}`,
                  borderRadius: 10, overflow: 'hidden',
                  transition: 'border-color 0.2s',
                }}
              >
                <button
                  onClick={() => toggle(step.id)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px 16px', background: 'transparent', border: 'none',
                    cursor: 'pointer', textAlign: 'left',
                  }}
                >
                  <StepIndicator status={step.status} color={step.color} icon={step.icon} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="font-display" style={{ fontSize: 13.5, fontWeight: 700, color: step.status === 'pending' ? 'var(--muted-foreground)' : 'var(--foreground)' }}>
                        {step.label}
                      </span>
                      {step.status === 'running' && (
                        <span className="animate-pulse-soft" style={{ fontSize: 11, color: step.color, fontFamily: 'JetBrains Mono' }}>RUNNING</span>
                      )}
                      {step.status === 'failed' && (
                        <span style={{ fontSize: 11, color: '#F87171', fontFamily: 'JetBrains Mono' }}>{run.status === 'cancelled' ? 'CANCELLED' : 'FAILED'}</span>
                      )}
                    </div>
                  </div>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeOpacity="0.4"
                    style={{ transform: expanded.has(step.id) ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}>
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </button>

                {expanded.has(step.id) && (
                  <div style={{ padding: '0 16px 14px', borderTop: '1px solid var(--border)' }}>
                    <p style={{ margin: '10px 0 0', fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.6 }}>{step.desc}</p>
                    {step.id === 'plan' && (
                      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {steps.map((s, idx) => (
                          <div key={s.step_id} style={{ display: 'flex', gap: 8, fontSize: 12, color: s.status === 'completed' ? 'var(--foreground)' : 'var(--muted-foreground)' }}>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 1 }}>
                              <polyline points="20 6 9 17 4 12" stroke={s.status === 'completed' ? 'var(--green)' : 'var(--border)'} strokeWidth="2.5"/>
                            </svg>
                            {idx + 1}. {s.description} <span className="font-mono" style={{ fontSize: 11 }}>[{s.step_id}{s.depends_on.length ? ` ← ${s.depends_on.join(', ')}` : ''}] {s.status}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {step.id === 'execute' && (
                      <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        {[
                          { label: 'Chunks retrieved', value: String(sources.length) },
                          { label: 'Steps executed', value: String(run.step_count) },
                          { label: 'Replans', value: `${run.replan_count}/${run.max_replans}` },
                          { label: 'Duration', value: `${(run.observations.reduce((s, o) => s + o.duration_ms, 0) / 1000).toFixed(1)}s` },
                        ].map(item => (
                          <div key={item.label} style={{ background: 'var(--surface-2)', borderRadius: 7, padding: '8px 10px', border: '1px solid var(--border)' }}>
                            <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{item.label}</div>
                            <div className="font-mono" style={{ fontSize: 14, fontWeight: 700, color: 'var(--foreground)' }}>{item.value}</div>
                          </div>
                        ))}
                        {steps.filter(s => s.error).map(s => (
                          <div key={s.step_id} style={{ gridColumn: '1 / -1', fontSize: 12, color: '#F87171' }}>{s.step_id}: {s.error?.code} — {s.error?.message}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {/* Connector */}
              {i < phases.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', paddingLeft: 28, paddingTop: 2, paddingBottom: 2 }}>
                  <div style={{ width: 1.5, height: 16, background: step.status === 'done' ? 'rgba(16,185,129,0.4)' : 'var(--border)', borderRadius: 1 }} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Side info panel */}
        <div style={{ width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto' }} className="tuffy-side-panel">
          <InfoPanel title="Current Task">
            <div style={{ fontSize: 13, color: 'var(--foreground)', lineHeight: 1.5 }}>{run.user_request}</div>
            <div style={{ marginTop: 8 }}>
              <span className="badge badge-violet font-mono" style={{ fontSize: 10 }}>{run.task_id}</span>
            </div>
          </InfoPanel>

          <InfoPanel title="Active Step">
            <span className="font-display" style={{ fontSize: 13, fontWeight: 700, color: '#F59E0B' }}>{active ? active.description : running ? statusText(run.status) : 'None (run finished)'}</span>
            {active && <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--muted-foreground)' }}>{active.step_id} · {active.status}</p>}
          </InfoPanel>

          <InfoPanel title="Model">
            {run.routing ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--foreground)' }}>{run.routing.model}</span>
                  <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{run.routing.purpose}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{run.routing.reason}</div>
              </>
            ) : <div style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>No routing recorded for this run.</div>}
          </InfoPanel>

          <InfoPanel title="Tools Used">
            {toolsUsed.map(t => (
              <div key={t} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 5 }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', flexShrink: 0 }} />
                <span style={{ fontSize: 12, color: 'var(--foreground)' }}>{t}</span>
              </div>
            ))}
          </InfoPanel>

          <InfoPanel title="Sources">
            <div style={{ fontSize: 12, color: 'var(--muted-foreground)', marginBottom: 6 }}>
              {sources.length} chunk(s) retrieved from {new Set(sources.map(s => s.document_id)).size} document(s)
            </div>
            {Array.from(new Set(sources.map(s => s.filename))).map(doc => (
              <div key={doc} style={{ fontSize: 11.5, color: 'var(--muted-foreground)', padding: '4px 6px', background: 'var(--surface-2)', borderRadius: 5, marginBottom: 3 }}>
                📄 {doc}
              </div>
            ))}
          </InfoPanel>
        </div>
      </div>
      )}

      {/* Execution log */}
      {run && (
      <div style={{ flexShrink: 0 }}>
        <button
          onClick={() => setLogOpen(v => !v)}
          className="btn-ghost"
          style={{ width: '100%', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8 }}
        >
          <span style={{ fontSize: 12.5, fontWeight: 600 }}>Execution Log</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ transform: logOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        {logOpen && (
          <div style={{
            background: '#0A0A0F', border: '1px solid var(--border)', borderTop: 'none',
            borderRadius: '0 0 8px 8px', padding: '12px 16px', maxHeight: 180, overflowY: 'auto',
          }}>
            {log.map((entry, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 4, fontFamily: 'JetBrains Mono', fontSize: 11.5 }}>
                <span style={{ color: 'var(--muted-foreground)', flexShrink: 0 }}>{entry.time ? new Date(entry.time).toLocaleTimeString() : '        '}</span>
                <span style={{ color: entry.level === 'info' ? '#A78BFA' : entry.level === 'success' ? 'var(--green)' : '#F59E0B' }}>
                  [{entry.level.toUpperCase()}]
                </span>
                <span style={{ color: 'var(--foreground)' }}>{entry.msg}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      )}

      <style>{`
        @media (max-width: 768px) { .tuffy-side-panel { display: none; } }
      `}</style>
    </div>
  );
}

function statusText(status: string) {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

function Empty({ text }: { text: string }) {
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>{text}</p>
    </div>
  );
}

function StepIndicator({ status, color, icon }: { status: PhaseStatus; color: string; icon: string }) {
  return (
    <div style={{
      width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
      background: status === 'pending' ? 'var(--surface-2)' : status === 'failed' ? 'rgba(239,68,68,0.12)' : `${color}18`,
      border: `1.5px solid ${status === 'pending' ? 'var(--border)' : status === 'failed' ? 'rgba(239,68,68,0.6)' : color + (status === 'running' ? '' : '60')}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 15,
    }}>
      {status === 'done' ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      ) : status === 'failed' ? (
        <span style={{ color: '#F87171' }}>✕</span>
      ) : (
        <span style={{ opacity: status === 'pending' ? 0.3 : 1 }}>{icon}</span>
      )}
    </div>
  );
}

function InfoPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 10, padding: '12px 14px' }}>
      <div className="section-label" style={{ marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );
}
