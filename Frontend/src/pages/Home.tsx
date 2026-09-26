import { useNavigate } from 'react-router';

export function Home() {
  const navigate = useNavigate();
  return (
    <div style={{ background: 'var(--background)', minHeight: '100vh' }}>
      {/* Hero */}
      <section style={{
        minHeight: 'calc(100vh - 58px)',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background grid */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 0%, transparent 100%)',
        }} />

        {/* Glow orbs */}
        <div style={{
          position: 'absolute', top: '15%', left: '8%',
          width: 360, height: 360, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '10%', right: '10%',
          width: 280, height: 280, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(15,118,110,0.1) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />

        <div style={{ maxWidth: 1440, margin: '0 auto', padding: '60px 40px', width: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>
          {/* Left: text */}
          <div>
            <div className="badge badge-violet" style={{ marginBottom: 20 }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#A78BFA', display: 'inline-block' }} />
              SIH26117 — Sovereign AI Platform
            </div>
            <h1 className="font-display" style={{
              fontSize: 'clamp(40px, 5vw, 68px)',
              fontWeight: 800,
              lineHeight: 1.08,
              color: 'var(--foreground)',
              margin: '0 0 16px',
              letterSpacing: '-0.02em',
            }}>
              Builder AI
              <br />
              <span className="gradient-text">Sovereign AI</span>
              <br />
              Workbench
            </h1>
            <p style={{ fontSize: 17, color: 'var(--muted-foreground)', lineHeight: 1.65, maxWidth: 480, margin: '0 0 32px', fontWeight: 400 }}>
              Industrial-grade agentic AI that reasons locally, retrieves knowledge, validates outputs, and delivers structured approvals — without sending your data anywhere.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button onClick={() => navigate('/workbench')} className="btn-primary" style={{ fontSize: 15, padding: '11px 28px' }}>
                Get Started
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
              <button onClick={() => navigate('/about')} className="btn-secondary" style={{ fontSize: 15, padding: '11px 24px' }}>
                Learn More
              </button>
            </div>
          </div>

          {/* Right: animated AI diagram */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <AIDiagram />
          </div>
        </div>

        {/* Mobile hero: stacked */}
        <style>{`
          @media (max-width: 768px) {
            .hero-grid { grid-template-columns: 1fr !important; gap: 40px !important; padding: 40px 20px !important; text-align: center; }
            .hero-diagram { order: -1; }
            .hero-actions { justify-content: center !important; }
          }
        `}</style>
      </section>

      {/* Capability strip */}
      <section style={{ borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', padding: '48px 40px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div className="section-label" style={{ marginBottom: 10 }}>Core Capabilities</div>
            <h2 className="font-display" style={{ fontSize: 28, fontWeight: 700, margin: 0, color: 'var(--foreground)' }}>
              Everything you need, nothing you don't
            </h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
            {CAPABILITIES.map(cap => (
              <div key={cap.title} className="metric-card card-glass-hover">
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: `${cap.accent}18`,
                  border: `1px solid ${cap.accent}30`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 14, fontSize: 18,
                }}>{cap.icon}</div>
                <div className="font-display" style={{ fontSize: 16, fontWeight: 700, marginBottom: 6, color: 'var(--foreground)' }}>{cap.title}</div>
                <div style={{ fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.55 }}>{cap.desc}</div>
                <div style={{ marginTop: 14 }}>
                  <span className="font-mono" style={{ fontSize: 22, fontWeight: 600, color: cap.accent }}>{cap.value}</span>
                  <span style={{ fontSize: 12, color: 'var(--muted-foreground)', marginLeft: 4 }}>{cap.unit}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section style={{ padding: '72px 40px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <div style={{ marginBottom: 44 }}>
            <div className="section-label" style={{ marginBottom: 10 }}>How it works</div>
            <h2 className="font-display" style={{ fontSize: 30, fontWeight: 700, margin: 0, color: 'var(--foreground)' }}>
              From request to approved deliverable
            </h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 0, position: 'relative' }}>
            {WORKFLOW_STEPS.map((step, i) => (
              <div key={step.title} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', padding: '0 24px', borderLeft: i > 0 ? '1px solid var(--border)' : 'none', position: 'relative' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: 'var(--violet-dim)', border: '1px solid rgba(124,58,237,0.3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'JetBrains Mono', fontSize: 13, fontWeight: 700, color: '#A78BFA',
                  marginBottom: 14,
                }}>{String(i + 1).padStart(2, '0')}</div>
                <div className="font-display" style={{ fontSize: 15, fontWeight: 700, marginBottom: 6, color: 'var(--foreground)' }}>{step.title}</div>
                <div style={{ fontSize: 12.5, color: 'var(--muted-foreground)', lineHeight: 1.55 }}>{step.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '0 40px 80px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: '56px 48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 32,
            flexWrap: 'wrap',
            position: 'relative',
            overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', top: -60, right: -60,
              width: 240, height: 240, borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)',
            }} />
            <div>
              <h2 className="font-display" style={{ fontSize: 32, fontWeight: 800, margin: '0 0 10px', color: 'var(--foreground)' }}>
                Ready to deploy?
              </h2>
              <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: 15 }}>
                Launch the workbench and start your first agentic project.
              </p>
            </div>
            <button onClick={() => navigate('/workbench')} className="btn-primary" style={{ fontSize: 15, padding: '12px 32px', flexShrink: 0 }}>
              Open Workbench
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '28px 40px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 24, height: 24, borderRadius: 5,
              background: 'linear-gradient(135deg, #7C3AED, #0F766E)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            <span className="font-display" style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>Builder AI</span>
            <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>— Sovereign AI Workbench</span>
          </div>
          <div style={{ display: 'flex', gap: 20 }}>
            {['Privacy', 'Security', 'Documentation', 'Support'].map(item => (
              <span key={item} style={{ fontSize: 12.5, color: 'var(--muted-foreground)', cursor: 'pointer' }}>{item}</span>
            ))}
          </div>
          <span style={{ fontSize: 11.5, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>© 2026 SIH26117</span>
        </div>
      </footer>
    </div>
  );
}

function AIDiagram() {
  return (
    <div style={{ position: 'relative', width: 380, height: 380 }}>
      {/* Outer ring */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: '50%',
        border: '1px dashed rgba(124,58,237,0.2)',
      }} className="animate-spin-slow" />

      {/* Middle ring */}
      <div style={{
        position: 'absolute', inset: 40, borderRadius: '50%',
        border: '1px solid rgba(15,118,110,0.15)',
      }} />

      {/* Center node */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%,-50%)',
        width: 100, height: 100, borderRadius: '50%',
        background: 'linear-gradient(135deg, rgba(124,58,237,0.3) 0%, rgba(15,118,110,0.2) 100%)',
        border: '1.5px solid rgba(124,58,237,0.5)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 4,
      }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="#A78BFA" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{ fontSize: 9, fontFamily: 'JetBrains Mono', color: '#A78BFA', letterSpacing: '0.06em' }}>TUFFY</span>
      </div>

      {/* Orbiting nodes */}
      {ORBIT_NODES.map((node, i) => {
        const angle = (i / ORBIT_NODES.length) * 2 * Math.PI - Math.PI / 2;
        const r = 145;
        const x = 190 + r * Math.cos(angle);
        const y = 190 + r * Math.sin(angle);
        return (
          <div key={node.label} style={{
            position: 'absolute',
            top: y - 26, left: x - 26,
            width: 52, height: 52, borderRadius: 12,
            background: `${node.color}18`,
            border: `1px solid ${node.color}40`,
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
          }}>
            <span style={{ fontSize: 16 }}>{node.icon}</span>
            <span style={{ fontSize: 8.5, fontFamily: 'JetBrains Mono', color: node.color, letterSpacing: '0.05em' }}>{node.label}</span>
          </div>
        );
      })}

      {/* Connecting lines */}
      <svg style={{ position: 'absolute', inset: 0 }} width={380} height={380}>
        {ORBIT_NODES.map((node, i) => {
          const angle = (i / ORBIT_NODES.length) * 2 * Math.PI - Math.PI / 2;
          const r = 145;
          const x = 190 + r * Math.cos(angle);
          const y = 190 + r * Math.sin(angle);
          return (
            <line key={i}
              x1={190} y1={190} x2={x} y2={y}
              stroke={node.color} strokeWidth="1"
              strokeOpacity="0.2" strokeDasharray="4 4"
            />
          );
        })}
      </svg>
    </div>
  );
}

const ORBIT_NODES = [
  { label: 'PLAN', icon: '🧠', color: '#A78BFA' },
  { label: 'RAG', icon: '📚', color: '#14B8A6' },
  { label: 'TOOLS', icon: '⚙️', color: '#F59E0B' },
  { label: 'VALIDATE', icon: '✓', color: '#10B981' },
  { label: 'LOCAL', icon: '🔒', color: '#6D28D9' },
];

const CAPABILITIES = [
  { icon: '🤖', title: 'AI Models', desc: 'Local quantized models for reasoning, vision, and embeddings.', value: '8+', unit: 'models', accent: '#A78BFA' },
  { icon: '⚙️', title: 'Agentic Workflow', desc: 'Multi-step autonomous agent pipelines with Tuffy orchestration.', value: '∞', unit: 'steps', accent: '#14B8A6' },
  { icon: '🔒', title: 'Local / On-Premise', desc: 'No data leaves your environment. Fully air-gapped capable.', value: '100%', unit: 'local', accent: '#10B981' },
  { icon: '🌐', title: 'External Calls', desc: 'Controlled, logged, and auditable outbound requests.', value: '<2%', unit: 'egress', accent: '#F59E0B' },
];

const WORKFLOW_STEPS = [
  { title: 'Request', desc: 'User submits a natural language task or uploads a document.' },
  { title: 'Planning', desc: 'Tuffy decomposes the request into steps and selects tools.' },
  { title: 'Execution', desc: 'Models retrieve knowledge, run tools, and process outputs.' },
  { title: 'Validation', desc: 'Results are validated against evidence and policies.' },
  { title: 'Deliverable', desc: 'Structured DOCX approval note ready for human sign-off.' },
];
