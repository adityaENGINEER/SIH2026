import { useEffect, useState } from 'react';
import { useProjectContext } from '../context/ProjectContext';
import { securityApi } from '../services/securityApi';
import { SecurityEvent, SecuritySummary } from '../services/types';
import { describeError } from '../components/common/StatusBadge';

// Controls that are enforced in backend code (not aspirational settings).
const POLICIES = [
  { name: 'Block non-local model endpoints (local-only inference)', active: true },
  { name: 'Require human sign-off on approval notes', active: true },
  { name: 'Log all model invocations', active: true },
  { name: 'Log all tool executions', active: true },
  { name: 'Project-scoped data access enforced by backend', active: true },
];

export function Security() {
  const { activeProject } = useProjectContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [systemSummary, setSystemSummary] = useState<SecuritySummary | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sys, proj, evs] = await Promise.all([
        securityApi.getSummary(),
        activeProject ? securityApi.getProjectSummary(activeProject.project_id) : Promise.resolve(null),
        activeProject ? securityApi.getProjectEvents(activeProject.project_id) : securityApi.getEvents(),
      ]);
      setSystemSummary(sys);
      setSummary(proj);
      setEvents(evs);
    } catch (err) {
      setError(describeError(err, 'security telemetry'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [activeProject]);

  const s = summary || systemSummary;
  const total = events.length;
  const pct = (n: number) => (total ? Math.round((n / total) * 1000) / 10 : 0);
  const localModel = events.filter(e => e.event_type === 'model_call').length;
  const tools = events.filter(e => e.event_type === 'tool_execution').length;
  const blocked = events.filter(e => e.blocked).length;
  const metrics = [
    { label: 'TOTAL EVALUATIONS', value: s?.total_evaluations ?? 0, sub: activeProject ? `model calls · ${activeProject.name}` : 'model calls · system', icon: '📊', color: '#A78BFA' },
    { label: 'OUTBOUND CALLS', value: s?.outbound_calls ?? 0, sub: 'non-local destinations attempted', icon: '🌐', color: '#F59E0B' },
    { label: 'BLOCKED', value: s?.blocked_calls ?? 0, sub: 'blocked by local-only policy', icon: '🛑', color: 'var(--red)' },
    { label: 'LOCAL CALLS', value: s?.local_calls ?? 0, sub: 'model + tool calls on this machine', icon: '🔒', color: 'var(--green)' },
  ];
  const egress = [
    { label: 'Local model inference', value: pct(localModel), color: 'var(--green)' },
    { label: 'Local tool execution', value: pct(tools), color: '#A78BFA' },
    { label: 'Blocked outbound', value: pct(blocked), color: 'var(--red)' },
  ];
  const filtered = events.filter(e => !filter || `${e.event_type} ${e.source} ${e.destination} ${e.reason}`.toLowerCase().includes(filter.toLowerCase()));
  const destinations = Array.from(events.reduce((m, e) => m.set(e.destination, (m.get(e.destination) || 0) + 1), new Map<string, number>()));

  const exportAudit = () => {
    const blob = new Blob([JSON.stringify(events, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `security-events-${activeProject?.project_id || 'system'}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Enterprise Security</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Security Overview</h1>
            <p style={{ margin: '6px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
              All AI activity is logged, audited, and policy-enforced locally.
              {systemSummary && <> System-wide: {systemSummary.total_evaluations} model calls, {systemSummary.blocked_calls} blocked.</>}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-secondary" style={{ fontSize: 12.5 }} onClick={exportAudit} disabled={events.length === 0}>Export Audit Log</button>
            <button className="btn-primary" style={{ fontSize: 12.5 }} onClick={load} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={load}>Retry</button>
        </div>
      )}

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
        {metrics.map(m => (
          <div key={m.label} className="metric-card" style={{ borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', letterSpacing: '0.08em' }}>{m.label}</span>
              <span style={{ fontSize: 16 }}>{m.icon}</span>
            </div>
            <div className="font-display" style={{ fontSize: 26, fontWeight: 800, color: m.color, lineHeight: 1 }}>{m.value.toLocaleString()}</div>
            <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)', marginTop: 4 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="tab-bar" style={{ alignSelf: 'flex-start' }}>
        {['overview', 'events', 'policy', 'network'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`tab-item ${activeTab === t ? 'active' : ''}`}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Egress breakdown */}
          <div className="card-glass" style={{ borderRadius: 12, padding: '20px' }}>
            <div className="font-display" style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Network Egress Breakdown</div>
            {total === 0 ? (
              <div style={{ fontSize: 12.5, color: 'var(--muted-foreground)' }}>No telemetry recorded yet{activeProject ? ' for this project' : ''}.</div>
            ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {egress.map(item => (
                <div key={item.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                    <span style={{ fontSize: 12.5, color: 'var(--foreground)' }}>{item.label}</span>
                    <span className="font-mono" style={{ fontSize: 12, color: item.color }}>{item.value}%</span>
                  </div>
                  <div style={{ height: 5, background: 'var(--surface-3)', borderRadius: 99 }}>
                    <div style={{ height: '100%', width: `${item.value}%`, background: item.color, borderRadius: 99 }} />
                  </div>
                </div>
              ))}
              <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>Based on {total} recorded events.</div>
            </div>
            )}
          </div>

          {/* Policy status */}
          <PolicyCard />
        </div>
      )}

      {/* Events table */}
      {activeTab === 'events' && (
        <div className="card-glass" style={{ borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="font-display" style={{ fontSize: 14, fontWeight: 700 }}>Security Events {activeProject ? `· ${activeProject.name}` : '· system'}</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <input className="input-field" placeholder="Filter events..." style={{ width: 200 }} value={filter} onChange={e => setFilter(e.target.value)} />
            </div>
          </div>
          <div>
            {filtered.length === 0 && <div style={{ padding: '20px', fontSize: 13, color: 'var(--muted-foreground)' }}>{loading ? 'Loading events…' : 'No security events recorded.'}</div>}
            {filtered.slice(0, 300).map(ev => (
              <div key={ev.event_id} style={{
                display: 'flex', alignItems: 'center', gap: 16,
                padding: '11px 20px', borderBottom: '1px solid var(--border)',
                transition: 'background 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-2)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <span className="font-mono" style={{ fontSize: 11.5, color: 'var(--muted-foreground)', flexShrink: 0 }}>{new Date(ev.timestamp).toLocaleString()}</span>
                <span className={`badge ${ev.blocked ? 'badge-red' : 'badge-green'}`} style={{ flexShrink: 0 }}>
                  {ev.blocked ? 'BLOCKED' : 'ALLOWED'}
                </span>
                <span style={{ flex: 1, fontSize: 13, color: 'var(--foreground)' }}>{ev.event_type} — {ev.source} → {ev.destination}{ev.reason ? ` (${ev.reason})` : ''}</span>
                {ev.task_id && <span className="badge badge-gray font-mono" style={{ fontSize: 10 }}>{ev.task_id}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'policy' && <PolicyCard />}

      {activeTab === 'network' && (
        <div className="card-glass" style={{ borderRadius: 12, padding: '20px' }}>
          <div className="font-display" style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Destinations Contacted</div>
          {destinations.length === 0 && <div style={{ fontSize: 12.5, color: 'var(--muted-foreground)' }}>No network activity recorded.</div>}
          {destinations.map(([dest, count]) => (
            <div key={dest} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8, marginBottom: 6 }}>
              <span className="font-mono" style={{ fontSize: 12.5 }}>{dest}</span>
              <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{count} events</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PolicyCard() {
  return (
    <div className="card-glass" style={{ borderRadius: 12, padding: '20px' }}>
      <div className="font-display" style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Policy Status</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {POLICIES.map(p => (
          <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 8 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: p.active ? 'var(--green)' : 'var(--red)', flexShrink: 0 }} />
            <span style={{ flex: 1, fontSize: 12.5 }}>{p.name}</span>
            <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{p.active ? 'ENFORCED' : 'INACTIVE'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
