import { useNavigate } from 'react-router';

const SERVICES = [
  {
    icon: '⚙️', title: 'Agentic AI', subtitle: 'Tuffy Orchestration',
    desc: 'Multi-step autonomous agents that plan, execute, observe, validate, and replan. Handles complex workflows without human intervention at each step.',
    features: ['Plan-Execute-Observe-Validate loop', 'Multi-model coordination', 'Tool selection & execution', 'Failure recovery & replanning'],
    accent: '#A78BFA', tag: 'Core',
  },
  {
    icon: '📚', title: 'RAG / Knowledge', subtitle: 'Retrieval-Augmented Generation',
    desc: 'Index your documents and retrieve semantically relevant evidence using local embedding models. Grounded responses with citation trails.',
    features: ['Local vector indexing', 'Semantic chunk retrieval', 'Evidence citations', 'Multi-document synthesis'],
    accent: '#14B8A6', tag: 'Core',
  },
  {
    icon: '📄', title: 'Document Intelligence', subtitle: 'Extraction & Analysis',
    desc: 'Parse PDFs, DOCX, XLSX, and scanned documents. Extract key information, tables, and structured data automatically.',
    features: ['PDF & DOCX parsing', 'Table extraction', 'Structured data output', 'Metadata enrichment'],
    accent: '#10B981', tag: 'Core',
  },
  {
    icon: '👁️', title: 'Vision & OCR', subtitle: 'Image Understanding',
    desc: 'Analyze photos, diagrams, and scanned documents using Moondream 2. Extract text and interpret visual content locally.',
    features: ['Scanned document OCR', 'Diagram analysis', 'Image captioning', 'Visual QA'],
    accent: '#F59E0B', tag: 'Vision',
  },
  {
    icon: '🔒', title: 'Secure Sandbox', subtitle: 'Controlled Execution',
    desc: 'All tool execution is isolated in a local sandbox. Outbound calls are blocked by default and require explicit policy approval.',
    features: ['Tool isolation', 'Egress blocking', 'Audit logging', 'Policy enforcement'],
    accent: '#6D28D9', tag: 'Security',
  },
  {
    icon: '📋', title: 'Industrial Deliverables', subtitle: 'Structured Outputs',
    desc: 'Generate professionally formatted DOCX approval notes with full evidence citations, compliance status, and human review workflow.',
    features: ['DOCX generation', 'Evidence citations', 'Approval workflow', 'Human sign-off'],
    accent: '#EF4444', tag: 'Output',
  },
];

export function Services() {
  const navigate = useNavigate();
  return (
    <div style={{ background: 'var(--background)', minHeight: '100vh' }}>
      {/* Header */}
      <section style={{ padding: '80px 40px 60px', maxWidth: 1440, margin: '0 auto' }}>
        <div style={{ maxWidth: 680 }}>
          <div className="badge badge-violet" style={{ marginBottom: 16 }}>Platform Services</div>
          <h1 className="font-display" style={{ fontSize: 'clamp(36px, 4vw, 54px)', fontWeight: 800, margin: '0 0 18px', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
            Everything your AI<br />
            <span className="gradient-text">needs to deliver</span>
          </h1>
          <p style={{ fontSize: 16.5, color: 'var(--muted-foreground)', lineHeight: 1.7, maxWidth: 520 }}>
            Six integrated capabilities working together to take any request from input to a validated, human-reviewed deliverable — all on your infrastructure.
          </p>
        </div>
      </section>

      {/* Services grid */}
      <section style={{ padding: '0 40px 80px', maxWidth: 1440, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 18 }}>
          {SERVICES.map(svc => (
            <ServiceCard key={svc.title} svc={svc} />
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section style={{ padding: '0 40px 80px' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <div style={{
            background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 16,
            padding: '48px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 24,
          }}>
            <div>
              <h2 className="font-display" style={{ fontSize: 26, fontWeight: 800, margin: '0 0 8px' }}>All six services, one deployment</h2>
              <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: 14 }}>Install once, run everything locally. No per-service subscriptions.</p>
            </div>
            <button onClick={() => navigate('/workbench')} className="btn-primary" style={{ fontSize: 14, padding: '11px 28px', flexShrink: 0 }}>
              Open Workbench →
            </button>
          </div>
        </div>
      </section>

      <style>{`
        @media (max-width: 768px) {
          section { padding-left: 20px !important; padding-right: 20px !important; }
          .services-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

function ServiceCard({ svc }: { svc: typeof SERVICES[0] }) {
  return (
    <div className="card-glass card-glass-hover" style={{ borderRadius: 14, padding: '24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{
          width: 52, height: 52, borderRadius: 12,
          background: `${svc.accent}14`, border: `1px solid ${svc.accent}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
        }}>{svc.icon}</div>
        <span className="badge badge-violet" style={{ fontSize: 10.5 }}>{svc.tag}</span>
      </div>

      <div>
        <div className="font-display" style={{ fontSize: 18, fontWeight: 800, marginBottom: 4, color: 'var(--foreground)' }}>{svc.title}</div>
        <div style={{ fontSize: 12, color: svc.accent, fontFamily: 'JetBrains Mono', marginBottom: 10, letterSpacing: '0.04em' }}>{svc.subtitle}</div>
        <p style={{ margin: 0, fontSize: 13.5, color: 'var(--muted-foreground)', lineHeight: 1.65 }}>{svc.desc}</p>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {svc.features.map(f => (
            <div key={f} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12.5, color: 'var(--foreground)' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <polyline points="20 6 9 17 4 12" stroke={svc.accent} strokeWidth="2.5"/>
              </svg>
              {f}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
