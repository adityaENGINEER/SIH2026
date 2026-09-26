import { useEffect, useState } from 'react';
import { modelsApi } from '../services/modelsApi';
import { Model } from '../services/types';
import { describeError } from '../components/common/StatusBadge';

const ROLE_META: Record<string, { type: string; purpose: string; caps: string[]; accent: string; icon: string }> = {
  general: { type: 'Language Model', purpose: 'Router default for chat, RAG answers and document extraction', caps: ['Chat', 'RAG', 'Extraction'], accent: '#A78BFA', icon: '🧠' },
  vision: { type: 'Vision Model', purpose: 'Router target when an image is attached or a vision request is detected', caps: ['Vision', 'Image analysis'], accent: '#14B8A6', icon: '👁️' },
  embedding: { type: 'Embedding Model', purpose: 'Used internally for document indexing and semantic retrieval', caps: ['Embeddings', 'Semantic search'], accent: '#10B981', icon: '🔗' },
  unassigned: { type: 'Installed Model', purpose: 'Installed in Ollama but not assigned a role by the router', caps: [], accent: '#6D28D9', icon: '📦' },
};

function formatBytes(bytes?: number): string {
  if (!bytes) return '—';
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

export function Models() {
  const [models, setModels] = useState<Model[]>([]);
  const [filter, setFilter] = useState<'all' | 'installed' | 'missing'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setModels(await modelsApi.list());
    } catch (err) {
      setModels([]);
      setError(describeError(err, 'model registry'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = models.filter(m => filter === 'all' || (filter === 'installed' ? m.installed : !m.installed));
  const installed = models.filter(m => m.installed);
  const diskTotal = installed.reduce((sum, m) => sum + (m.size || 0), 0);

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Local Model Registry</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0, color: 'var(--foreground)' }}>Models</h1>
            <p style={{ margin: '6px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
              Locally hosted models — no data leaves your environment.
            </p>
          </div>
          <button className="btn-primary" style={{ fontSize: 13 }} onClick={load} disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {/* Stats */}
        <div style={{ display: 'flex', gap: 16, marginTop: 16, flexWrap: 'wrap' }}>
          {[
            { label: 'Installed', value: installed.length, color: 'var(--green)' },
            { label: 'Registry entries', value: models.length, color: 'var(--foreground)' },
            { label: 'On disk', value: formatBytes(diskTotal), color: '#A78BFA' },
          ].map(s => (
            <div key={s.label} style={{ display: 'flex', gap: 6, alignItems: 'baseline' }}>
              <span className="font-display" style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</span>
              <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', marginBottom: 16, borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={load}>Retry</button>
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['all', 'installed', 'missing'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`tab-item ${filter === f ? 'active' : ''}`}
            style={{ background: filter === f ? 'var(--surface-3)' : 'transparent', border: '1px solid var(--border)', borderRadius: 6 }}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading && models.length === 0 && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Loading models from Ollama…</p>}
      {!loading && !error && filtered.length === 0 && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>No models in this view.</p>}

      {/* Model grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {filtered.map(model => (
          <ModelCard key={model.name} model={model} />
        ))}
      </div>
    </div>
  );
}

function ModelCard({ model }: { model: Model }) {
  const meta = ROLE_META[model.role] || ROLE_META.unassigned;
  return (
    <div className="card-glass card-glass-hover" style={{ borderRadius: 12, padding: '20px', opacity: model.installed ? 1 : 0.72 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{
            width: 42, height: 42, borderRadius: 10,
            background: `${meta.accent}18`, border: `1px solid ${meta.accent}30`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20,
          }}>{meta.icon}</div>
          <div>
            <div className="font-display" style={{ fontSize: 15, fontWeight: 700, color: 'var(--foreground)' }}>{model.name}</div>
            <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{meta.type} · role: {model.role}</div>
          </div>
        </div>
        <div>
          {model.installed ? (
            <span className="badge badge-green">Installed</span>
          ) : (
            <span className="badge badge-red">Not installed</span>
          )}
        </div>
      </div>

      <p style={{ fontSize: 13, color: 'var(--muted-foreground)', margin: '0 0 14px', lineHeight: 1.5 }}>{meta.purpose}</p>

      {meta.caps.length > 0 && (
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        {meta.caps.map(cap => (
          <span key={cap} style={{
            fontSize: 11, padding: '2px 8px', borderRadius: 4,
            background: 'var(--surface-2)', color: 'var(--muted-foreground)',
            border: '1px solid var(--border)',
          }}>{cap}</span>
        ))}
      </div>
      )}

      <div style={{ display: 'flex', gap: 16, padding: '10px 0', borderTop: '1px solid var(--border)' }}>
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', marginBottom: 2 }}>PARAMETERS</div>
          <div className="font-mono" style={{ fontSize: 13, fontWeight: 600, color: meta.accent }}>{model.parameter_size || '—'}</div>
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', marginBottom: 2 }}>DISK SIZE</div>
          <div className="font-mono" style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>{formatBytes(model.size)}</div>
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', marginBottom: 2 }}>LOCATION</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
            Local (Ollama)
          </div>
        </div>
      </div>
    </div>
  );
}
