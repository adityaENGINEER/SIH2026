import { useEffect, useState } from 'react';
import { toolsApi } from '../services/toolsApi';
import { api } from '../services/api';
import { Tool } from '../services/types';
import { describeError } from '../components/common/StatusBadge';

// Display metadata for tools the backend registry reports; unknown tools fall back to "Other".
const TOOL_META: Record<string, { cat: string; icon: string }> = {
  calculator: { cat: 'Computation', icon: '🧮' },
  file_reader: { cat: 'Files', icon: '📂' },
  file_writer: { cat: 'Files', icon: '✍️' },
  document_reader: { cat: 'Documents', icon: '📑' },
  generate_approval_document: { cat: 'Documents', icon: '📄' },
  execute_python_code: { cat: 'Sandbox', icon: '🧪' },
  analyze_image: { cat: 'Vision', icon: '🖼️' },
};

export function Tools() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [category, setCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [calculatorInput, setCalculatorInput] = useState('');
  const [calculatorResult, setCalculatorResult] = useState('');
  const [calculating, setCalculating] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setTools(await toolsApi.list());
    } catch (err) {
      setTools([]);
      setError(describeError(err, 'tool registry'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const meta = (t: Tool) => TOOL_META[t.name] || { cat: 'Other', icon: '🔧' };
  const categories = ['All', ...Array.from(new Set(tools.map(t => meta(t).cat)))];
  const filtered = tools.filter(t =>
    (category === 'All' || meta(t).cat === category) &&
    `${t.name} ${t.description}`.toLowerCase().includes(search.toLowerCase())
  );
  const calculatorAvailable = tools.some(t => t.name === 'calculator' && t.available);

  async function runCalc() {
    if (!calculatorInput.trim()) return;
    setCalculating(true);
    try {
      const res = await api.post('/tools/calculator/execute', { expression: calculatorInput });
      if (res.status === 'completed') setCalculatorResult(String(res.result.value));
      else setCalculatorResult(`Error: ${res.error?.message || 'calculation failed'}`);
    } catch (err: any) {
      setCalculatorResult(err instanceof TypeError ? 'Error: backend unavailable' : `Error: ${err.message}`);
    } finally {
      setCalculating(false);
    }
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Tool Registry & Sandbox</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Tools</h1>
            <p style={{ margin: '6px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
              Tools reported by the local backend registry. All execute on this machine.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={load}>Retry</button>
        </div>
      )}

      {/* Quick Calculator */}
      {calculatorAvailable && (
      <div className="card-glass" style={{ borderRadius: 12, padding: '18px 20px' }}>
        <div className="font-display" style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 12 }}>
          🧮 Quick Calculator <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400 }}>(backend calculator tool)</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            value={calculatorInput}
            onChange={e => setCalculatorInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && runCalc()}
            className="input-field"
            placeholder="e.g. (42 * 1.15) / 3.28084"
            style={{ flex: 1 }}
          />
          <button onClick={runCalc} className="btn-primary" style={{ padding: '9px 20px', fontSize: 13 }} disabled={calculating}>{calculating ? 'Calculating…' : 'Calculate'}</button>
        </div>
        {calculatorResult && (
          <div style={{ marginTop: 10, padding: '10px 14px', background: 'var(--surface-2)', borderRadius: 7, border: '1px solid var(--border)' }}>
            <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>Result: </span>
            <span className="font-mono" style={{ fontSize: 16, fontWeight: 700, color: calculatorResult.startsWith('Error') ? '#F87171' : '#A78BFA' }}>{calculatorResult}</span>
          </div>
        )}
      </div>
      )}

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="tab-bar">
          {categories.map(c => (
            <button key={c} onClick={() => setCategory(c)} className={`tab-item ${category === c ? 'active' : ''}`}>
              {c}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="input-field"
          placeholder="Search tools…"
          style={{ width: 200 }}
        />
      </div>

      {/* Tool grid */}
      {loading && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Loading tool registry…</p>}
      {!loading && !error && filtered.length === 0 && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>No tools match.</p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
        {filtered.map(tool => (
          <div key={tool.name} className="card-glass card-glass-hover" style={{ borderRadius: 12, padding: '18px', opacity: tool.available ? 1 : 0.65 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 9,
                  background: 'var(--surface-2)', border: '1px solid var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                }}>{meta(tool).icon}</div>
                <div>
                  <div className="font-display" style={{ fontSize: 13.5, fontWeight: 700 }}>{tool.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>{meta(tool).cat}</div>
                </div>
              </div>
              {tool.available
                ? <span className="badge badge-green" style={{ fontSize: 10 }}>Active</span>
                : <span className="badge badge-gray" style={{ fontSize: 10 }}>Inactive</span>
              }
            </div>

            <p style={{ margin: '0 0 12px', fontSize: 12.5, color: 'var(--muted-foreground)', lineHeight: 1.55 }}>{tool.description}</p>

            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span className="badge badge-green" style={{ fontSize: 10 }}>🔒 Local</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
