import { useNavigate } from 'react-router';

export function About() {
  const navigate = useNavigate();
  return (
    <div style={{ background: 'var(--background)', minHeight: '100vh' }}>
      {/* Hero */}
      <section style={{ padding: '80px 40px 60px', maxWidth: 1440, margin: '0 auto' }}>
        <div style={{ maxWidth: 720 }}>
          <div className="badge badge-violet" style={{ marginBottom: 16 }}>About Builder AI</div>
          <h1 className="font-display" style={{ fontSize: 'clamp(36px, 4vw, 56px)', fontWeight: 800, margin: '0 0 20px', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
            AI that works for you,<br />
            <span className="gradient-text">not the cloud</span>
          </h1>
          <p style={{ fontSize: 17, color: 'var(--muted-foreground)', lineHeight: 1.7, maxWidth: 560 }}>
            Builder AI is a sovereign, local-first AI workbench built for industrial, enterprise, and regulated environments where data privacy and auditability are non-negotiable.
          </p>
        </div>
      </section>

      {/* What it is */}
      <section style={{ padding: '0 40px 72px', maxWidth: 1440, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'start' }}>
          <div>
            <div className="section-label" style={{ marginBottom: 12 }}>What is Builder AI?</div>
            <h2 className="font-display" style={{ fontSize: 28, fontWeight: 700, margin: '0 0 16px' }}>An AI platform that stays on your premises</h2>
            <p style={{ fontSize: 14.5, color: 'var(--muted-foreground)', lineHeight: 1.75, margin: 0 }}>
              Builder AI combines local language models, retrieval-augmented generation, and the Tuffy agentic orchestrator to deliver intelligent, multi-step reasoning — entirely within your infrastructure. Every model call, tool invocation, and document retrieval is logged and audited. No external APIs are required for core functionality.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {WHY_LOCAL.map(item => (
              <div key={item.title} style={{ display: 'flex', gap: 14, padding: '14px', background: 'var(--surface-1)', borderRadius: 10, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 22, flexShrink: 0, marginTop: 2 }}>{item.icon}</div>
                <div>
                  <div className="font-display" style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{item.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.55 }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For who */}
      <section style={{ padding: '60px 40px', background: 'var(--surface-1)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <div className="section-label" style={{ marginBottom: 12, textAlign: 'center' }}>Who it's for</div>
          <h2 className="font-display" style={{ fontSize: 28, fontWeight: 700, margin: '0 0 36px', textAlign: 'center' }}>Built for professionals who can't compromise</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {FOR_WHO.map(item => (
              <div key={item.title} style={{ textAlign: 'center', padding: '24px 16px', background: 'var(--background)', borderRadius: 12, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>{item.icon}</div>
                <div className="font-display" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>{item.title}</div>
                <div style={{ fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.55 }}>{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section style={{ padding: '72px 40px', maxWidth: 1440, margin: '0 auto' }}>
        <div className="section-label" style={{ marginBottom: 12 }}>Architecture</div>
        <h2 className="font-display" style={{ fontSize: 28, fontWeight: 700, margin: '0 0 32px' }}>What Builder AI provides</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {PROVIDES.map(item => (
            <div key={item.title} style={{ padding: '20px', background: 'var(--surface-1)', borderRadius: 12, border: '1px solid var(--border)', borderLeft: `3px solid ${item.accent}` }}>
              <div style={{ fontSize: 20, marginBottom: 10 }}>{item.icon}</div>
              <div className="font-display" style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, color: item.accent }}>{item.title}</div>
              <div style={{ fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.6 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '0 40px 80px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto', textAlign: 'center' }}>
          <button onClick={() => navigate('/workbench')} className="btn-primary" style={{ fontSize: 15, padding: '12px 32px' }}>
            Start with Builder AI
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
        </div>
      </section>

      <style>{`
        @media (max-width: 768px) {
          section div[style*="grid-template-columns: 1fr 1fr"] { grid-template-columns: 1fr !important; gap: 32px !important; }
          section { padding-left: 20px !important; padding-right: 20px !important; }
        }
      `}</style>
    </div>
  );
}

const WHY_LOCAL = [
  { icon: '🔒', title: 'Data never leaves your premises', desc: 'All model inference happens on your hardware. No telemetry, no cloud APIs required.' },
  { icon: '📋', title: 'Full audit trail', desc: 'Every model call, tool use, and decision is logged with timestamps and provenance.' },
  { icon: '⚡', title: 'Low latency, high availability', desc: 'No network dependency means consistent performance without rate limits or downtime.' },
];

const FOR_WHO = [
  { icon: '🏭', title: 'Industrial Engineers', desc: 'Site inspection, compliance, and equipment analysis.' },
  { icon: '⚖️', title: 'Regulated Industries', desc: 'Healthcare, energy, finance — where data residency is mandatory.' },
  { icon: '🔐', title: 'Security-First Teams', desc: 'Defense, government, and critical infrastructure operators.' },
  { icon: '🏗️', title: 'Enterprise IT', desc: 'Internal automation without SaaS exposure.' },
];

const PROVIDES = [
  { icon: '🧠', title: 'Local LLM Runtime', desc: 'Run Qwen, Mistral, Llama, and other quantized models on your GPU.', accent: '#A78BFA' },
  { icon: '📚', title: 'RAG Knowledge Base', desc: 'Index your documents and retrieve evidence using Nomic Embed.', accent: '#14B8A6' },
  { icon: '⚙️', title: 'Tuffy Orchestrator', desc: 'Multi-step agentic planning with Plan-Execute-Observe-Validate loop.', accent: '#F59E0B' },
  { icon: '🔧', title: 'Tool Sandbox', desc: 'OCR, calculator, validators — all running locally in a controlled sandbox.', accent: '#10B981' },
  { icon: '📋', title: 'Structured Deliverables', desc: 'Generate DOCX approval notes with full evidence citations.', accent: '#6D28D9' },
  { icon: '🔒', title: 'Security Console', desc: 'Audit logs, egress monitoring, and policy enforcement built-in.', accent: '#EF4444' },
];
