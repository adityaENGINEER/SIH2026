import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import { useProjectContext } from '../context/ProjectContext';
import { agentRunsApi, TERMINAL_RUN_STATUSES } from '../services/agentRunsApi';
import { deliverablesApi } from '../services/deliverablesApi';
import { approvalsApi } from '../services/approvalsApi';
import { AgentRun, Approval, Deliverable } from '../services/types';
import { StatusBadge, formatTime, describeError } from '../components/common/StatusBadge';

export function AgentRuns() {
  const { activeProject } = useProjectContext();
  const [searchParams] = useSearchParams();
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [deliverable, setDeliverable] = useState<Deliverable | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['steps']));

  const loadRuns = async () => {
    if (!activeProject) { setRuns([]); return; }
    setLoading(true);
    setError(null);
    try {
      const list = await agentRunsApi.list(activeProject.project_id);
      setRuns(list);
      const requested = searchParams.get('run');
      setSelected(prev => (prev && list.some(r => r.task_id === prev)) ? prev
        : (requested && list.some(r => r.task_id === requested)) ? requested : (list[0]?.task_id ?? null));
    } catch (err) {
      setRuns([]);
      setError(describeError(err, 'agent runs'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { setSelected(null); setRun(null); loadRuns(); }, [activeProject]);

  useEffect(() => {
    if (!activeProject || !selected) { setRun(null); return; }
    let timer: ReturnType<typeof setTimeout> | undefined;
    let cancelled = false;
    const load = async () => {
      try {
        const r = await agentRunsApi.get(activeProject.project_id, selected);
        if (cancelled) return;
        setRun(r);
        setRuns(prev => prev.map(x => x.task_id === r.task_id ? r : x));
        if (!TERMINAL_RUN_STATUSES.includes(r.status)) timer = setTimeout(load, 2000);
      } catch (err) {
        if (!cancelled) setError(describeError(err, 'run details'));
      }
    };
    load();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [activeProject, selected]);

  useEffect(() => {
    setDeliverable(null);
    setApproval(null);
    if (!activeProject || !run) return;
    if (run.deliverable_id) {
      deliverablesApi.getMetadata(activeProject.project_id, run.deliverable_id).then(setDeliverable)
        .catch(err => setError(describeError(err, 'deliverable')));
    }
    if (run.approval_id) {
      approvalsApi.get(activeProject.project_id, run.approval_id).then(setApproval)
        .catch(err => setError(describeError(err, 'approval')));
    }
  }, [activeProject, run?.task_id, run?.deliverable_id, run?.approval_id]);

  function toggle(section: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  }

  const searchStep = run?.plan?.steps.find(s => s.capability === 'knowledge_search' && s.result);
  const evidence: any[] = searchStep?.result?.evidence || [];
  const sources: any[] = searchStep?.result?.sources || [];
  const grounding = run?.final_result?.grounding;

  return (
    <div style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', gap: 20, overflow: 'hidden' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div className="section-label" style={{ marginBottom: 6 }}>Audit Trail</div>
        <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Agent Run History</h1>
        <p style={{ margin: '6px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>Full audit trail for all agentic executions.</p>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={loadRuns}>Retry</button>
        </div>
      )}

      {!activeProject ? (
        <EmptyState text="Select a project to view its agent runs." />
      ) : loading && runs.length === 0 ? (
        <EmptyState text="Loading agent runs…" />
      ) : runs.length === 0 ? (
        <EmptyState text="No agent runs in this project yet. Start one from ChatBench." />
      ) : (
      <div style={{ flex: 1, display: 'flex', gap: 20, overflow: 'hidden', minHeight: 0 }}>
        {/* Run list */}
        <div style={{ width: 280, flexShrink: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {runs.map(r => (
            <div
              key={r.task_id}
              onClick={() => setSelected(r.task_id)}
              style={{
                background: selected === r.task_id ? 'var(--violet-dim)' : 'var(--surface-1)',
                border: `1px solid ${selected === r.task_id ? 'rgba(124,58,237,0.3)' : 'var(--border)'}`,
                borderRadius: 10, padding: '12px 14px', cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6, gap: 6 }}>
                <span className="font-mono" style={{ fontSize: 11, fontWeight: 600, color: selected === r.task_id ? '#A78BFA' : 'var(--foreground)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.task_id}</span>
                <StatusBadge status={r.status} />
              </div>
              <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--foreground)', marginBottom: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.user_request}</div>
              <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>{formatTime(r.created_at)}</div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        {run && (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Run overview */}
          <div className="card-glass" style={{ borderRadius: 12, padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, gap: 12 }}>
              <div style={{ minWidth: 0 }}>
                <div className="font-mono" style={{ fontSize: 13, color: 'var(--muted-foreground)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.task_id}</div>
                <div className="font-display" style={{ fontSize: 18, fontWeight: 800 }}>{run.user_request}</div>
              </div>
              <div style={{ flexShrink: 0 }}><StatusBadge status={run.status} size="lg" /></div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
              {[
                { label: 'Created', value: formatTime(run.created_at) },
                { label: 'Completed', value: formatTime(run.completed_at) },
                { label: 'Current Step', value: run.current_step || '—' },
                { label: 'Steps', value: `${run.step_count} executed / ${run.plan?.steps.length ?? 0} planned` },
                { label: 'Replans', value: `${run.replan_count} / ${run.max_replans}` },
                { label: 'Model', value: run.routing ? `${run.routing.model} (${run.routing.purpose})` : '—' },
              ].map(item => (
                <div key={item.label} style={{ background: 'var(--surface-2)', borderRadius: 8, padding: '10px 12px' }}>
                  <div style={{ fontSize: 10.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', marginBottom: 3 }}>{item.label.toUpperCase()}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', wordBreak: 'break-word' }}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Collapsible sections */}
          {[
            {
              id: 'blocking', title: 'Errors & Blocking Conditions', content: (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {run.error ? (
                    <div style={{ padding: '10px 12px', background: 'rgba(239,68,68,0.08)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.25)', fontSize: 13, color: 'var(--foreground)' }}>
                      <span className="font-mono" style={{ fontSize: 11.5 }}>{run.error.code}</span> — {run.error.message}
                    </div>
                  ) : (
                    <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>No errors recorded for this run.</div>
                  )}
                  {approval && approval.status !== 'APPROVED' && (
                    <div style={{ padding: '10px 12px', background: 'rgba(245,158,11,0.08)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.2)', fontSize: 13, color: 'var(--foreground)' }}>
                      ⚠️ Human sign-off required before this approval note is valid (status: {approval.status}).
                    </div>
                  )}
                </div>
              )
            },
            {
              id: 'steps', title: 'Plan & Agent Steps', content: (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {(run.plan?.steps || []).length === 0 && <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>No plan created yet.</div>}
                  {(run.plan?.steps || []).map((step, i) => {
                    const obs = [...run.observations].reverse().find(o => o.step_id === step.step_id);
                    return (
                      <div key={step.step_id} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8 }}>
                        <div className={`step-dot ${step.status === 'completed' ? 'step-dot-done' : step.status === 'running' ? 'step-dot-running' : step.status === 'failed' ? 'step-dot-waiting' : 'step-dot-pending'}`}>{i + 1}</div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 12.5, fontWeight: 600 }}>{step.description}</div>
                          <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>
                            <span className="font-mono">{step.step_id}</span> · {step.capability}{step.input?.tool_name ? ` (${step.input.tool_name})` : ''}
                            {step.depends_on.length > 0 && <> · depends on {step.depends_on.join(', ')}</>}
                          </div>
                          {step.error && <div style={{ fontSize: 11.5, color: '#F87171' }}>{step.error.code}: {step.error.message}</div>}
                        </div>
                        <StatusBadge status={step.status} />
                        <span className="font-mono" style={{ fontSize: 11.5, color: 'var(--muted-foreground)', minWidth: 48, textAlign: 'right' }}>{obs ? `${(obs.duration_ms / 1000).toFixed(1)}s` : '—'}</span>
                      </div>
                    );
                  })}
                </div>
              )
            },
            {
              id: 'validation', title: `Validation (${run.validation_results.length})`, content: (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {run.validation_results.length === 0 && <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>No validation results yet.</div>}
                  {run.validation_results.map((v, i) => (
                    <div key={i} style={{ fontSize: 12.5, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8 }}>
                      <span className={`badge ${v.valid ? 'badge-green' : 'badge-red'}`} style={{ fontSize: 10, marginRight: 8 }}>{v.valid ? 'VALID' : 'INVALID'}</span>
                      <span className="font-mono" style={{ fontSize: 11.5 }}>{v.step_id}</span> — {v.reason}{v.issues.length > 0 ? ` [${v.issues.join(', ')}]` : ''}
                    </div>
                  ))}
                  {grounding && (
                    <div style={{ fontSize: 12.5, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8 }}>
                      Grounding: {grounding.facts_from_source} source facts, {grounding.measurement_rows} measurement rows, {grounding.rejected_values?.length ?? 0} rejected values
                      {(grounding.warnings || []).map((w: any, i: number) => <div key={i} style={{ color: '#FBBF24' }}>⚠ {w.code}: {w.message}</div>)}
                    </div>
                  )}
                </div>
              )
            },
            {
              id: 'evidence', title: `Evidence (${evidence.length || sources.length})`, content: (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {evidence.length === 0 && sources.length === 0 && <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>No retrieved evidence for this run.</div>}
                  {(evidence.length ? evidence : sources).map((c, i) => (
                    <div key={i} style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px' }}>
                      <div style={{ display: 'flex', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                        <span className="badge badge-violet" style={{ fontSize: 10 }}>{c.chunk_id}</span>
                        {c.page_number && <span className="badge badge-gray" style={{ fontSize: 10 }}>Page {c.page_number}</span>}
                        <span style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{c.filename}</span>
                      </div>
                      {c.text && <p style={{ margin: 0, fontSize: 12, color: 'var(--muted-foreground)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{c.text.slice(0, 600)}{c.text.length > 600 ? '…' : ''}</p>}
                    </div>
                  ))}
                </div>
              )
            },
            {
              id: 'deliverables', title: 'Deliverables', content: (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {!deliverable ? (
                    <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>No deliverable was generated by this run.</div>
                  ) : (
                  <div style={{ background: 'var(--surface-2)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 10, padding: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                      <div>
                        <div className="font-display" style={{ fontSize: 14, fontWeight: 700, wordBreak: 'break-all' }}>{deliverable.filename}</div>
                        {approval && <StatusBadge status={approval.status} />}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <a className="btn-primary" style={{ fontSize: 12, padding: '6px 14px' }} href={deliverablesApi.getDownloadUrl(activeProject.project_id, deliverable.deliverable_id)}>{deliverable.type}</a>
                    </div>
                  </div>
                  )}
                </div>
              )
            },
          ].map(section => (
            <div key={section.id} style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
              <button
                onClick={() => toggle(section.id)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'transparent', border: 'none', cursor: 'pointer' }}
              >
                <span className="font-display" style={{ fontSize: 13.5, fontWeight: 700 }}>{section.title}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                  style={{ transform: expanded.has(section.id) ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', opacity: 0.5 }}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              {expanded.has(section.id) && (
                <div style={{ padding: '0 16px 14px', borderTop: '1px solid var(--border)', paddingTop: 14 }}>
                  {section.content}
                </div>
              )}
            </div>
          ))}
        </div>
        )}
      </div>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>{text}</p>
    </div>
  );
}
