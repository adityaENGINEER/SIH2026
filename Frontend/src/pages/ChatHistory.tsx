import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { useProjectContext } from '../context/ProjectContext';
import { conversationsApi } from '../services/conversationsApi';
import { Conversation } from '../services/types';
import { describeError } from '../components/common/StatusBadge';

function dayGroup(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const t = d.getTime();
  if (t >= startOfToday) return 'Today';
  if (t >= startOfToday - 86400000) return 'Yesterday';
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function ChatHistory() {
  const { activeProject } = useProjectContext();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!activeProject) { setConversations([]); return; }
    setLoading(true);
    setError(null);
    try {
      const history = await conversationsApi.getHistory(activeProject.project_id);
      history.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
      setConversations(history);
    } catch (err) {
      setConversations([]);
      setError(describeError(err, 'chat history'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [activeProject]);

  const filtered = conversations.filter(c => {
    const q = search.toLowerCase();
    return !q || (c.title || '').toLowerCase().includes(q) || (c.messages || []).some(m => m.content.toLowerCase().includes(q));
  });
  const groups = Array.from(new Set(filtered.map(c => dayGroup(c.updated_at))));

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: 20, height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Session Archive</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Chat History</h1>
          </div>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field"
            placeholder="Search conversations…"
            style={{ width: 240 }}
          />
        </div>
      </div>

      {/* Project scope */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <span style={{
          padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
          background: 'var(--violet-dim)', color: '#A78BFA', border: '1px solid rgba(124,58,237,0.3)',
        }}>
          {activeProject ? `Project: ${activeProject.name}` : 'No project selected'}
        </span>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={load}>Retry</button>
        </div>
      )}

      {/* Conversation list */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 0 }}>
        {!activeProject && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Select a project to view its conversations.</p>}
        {activeProject && loading && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Loading conversations…</p>}
        {activeProject && !loading && !error && filtered.length === 0 && (
          <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>{search ? 'No conversations match your search.' : 'No conversations in this project yet.'}</p>
        )}
        {groups.map(group => {
          const items = filtered.filter(c => dayGroup(c.updated_at) === group);
          return (
            <div key={group}>
              <div style={{ padding: '10px 4px 6px', display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="section-label">{group}</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {items.map(conv => {
                  const msgs = conv.messages || [];
                  const last = msgs[msgs.length - 1];
                  return (
                    <div
                      key={conv.conversation_id}
                      onClick={() => navigate(`/workbench?conversation=${conv.conversation_id}`)}
                      style={{
                        padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                        background: 'var(--surface-1)', border: '1px solid var(--border)', transition: 'all 0.15s',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-2)'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface-1)'; }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 5 }}>
                        <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--foreground)', lineHeight: 1.3 }}>{conv.title}</div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                          <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>
                            {new Date(conv.updated_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span className="badge badge-gray" style={{ fontSize: 10 }}>{msgs.length} messages</span>
                        <span style={{ fontSize: 12, color: 'var(--muted-foreground)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>{last ? last.content : 'Empty conversation'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
