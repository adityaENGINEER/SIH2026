import { useNavigate } from 'react-router';
import { useState } from 'react';
import { projectsApi } from '../services/projectsApi';
import { useProjectContext } from '../context/ProjectContext';

const PROJECT_TYPES = [
  { id: 'inspection', label: 'Site Inspection', icon: '🔍', desc: 'Analyze inspection reports and generate approval notes.' },
  { id: 'audit', label: 'Safety Audit', icon: '🛡️', desc: 'Conduct safety audits with policy validation.' },
  { id: 'maintenance', label: 'Maintenance Review', icon: '⚙️', desc: 'Review maintenance logs and equipment records.' },
  { id: 'compliance', label: 'Compliance Check', icon: '✅', desc: 'Verify compliance against regulatory standards.' },
  { id: 'general', label: 'General Analysis', icon: '📊', desc: 'Open-ended document analysis and reasoning.' },
];

export function NewProject() {
  const navigate = useNavigate();
  const { setActiveProject } = useProjectContext();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState('');
  const [reference, setReference] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create() {
    if (!name || !type) return;
    setIsCreating(true);
    setError(null);
    try {
      const project = await projectsApi.create({
        name,
        description: description || reference, // Use reference if desc empty or combine them
        project_type: type
      });
      setActiveProject(project);
      navigate('/workbench');
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
      setIsCreating(false);
    }
  }

  return (
    <div style={{
      padding: '40px 24px', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', minHeight: '100%',
    }}>
      <div style={{
        width: '100%', maxWidth: 520,
        background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 16, padding: '36px',
      }}>
        <div style={{ marginBottom: 28 }}>
          <div className="section-label" style={{ marginBottom: 8 }}>Workbench</div>
          <h1 className="font-display" style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>New Project</h1>
          <p style={{ margin: '8px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
            Set up a context for your agentic AI session.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* Name */}
          <div>
            <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 7, color: 'var(--foreground)' }}>Project Name *</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              className="input-field"
              placeholder="e.g. Inspection-Site-A"
            />
          </div>

          {/* Description */}
          <div>
            <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 7, color: 'var(--foreground)' }}>Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="input-field"
              placeholder="Brief description of the project scope and objectives…"
              rows={3}
              style={{ resize: 'vertical', fontFamily: 'Inter, sans-serif' }}
            />
          </div>

          {/* Project type */}
          <div>
            <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 9, color: 'var(--foreground)' }}>Project Type *</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {PROJECT_TYPES.map(pt => (
                <div
                  key={pt.id}
                  onClick={() => setType(pt.id)}
                  style={{
                    display: 'flex', gap: 12, alignItems: 'center', padding: '10px 14px',
                    borderRadius: 9, cursor: 'pointer',
                    background: type === pt.id ? 'var(--violet-dim)' : 'var(--surface-2)',
                    border: `1px solid ${type === pt.id ? 'rgba(124,58,237,0.35)' : 'var(--border)'}`,
                    transition: 'all 0.15s',
                  }}
                >
                  <span style={{ fontSize: 18 }}>{pt.icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: type === pt.id ? '#A78BFA' : 'var(--foreground)' }}>{pt.label}</div>
                    <div style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>{pt.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reference */}
          <div>
            <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 7, color: 'var(--foreground)' }}>Reference / Tag</label>
            <input
              value={reference}
              onChange={e => setReference(e.target.value)}
              className="input-field"
              placeholder="e.g. SIH-2026-047 (optional)"
            />
          </div>

          {/* Actions */}
          {error && <div style={{ color: 'var(--red)', fontSize: 13, marginBottom: 8 }}>{error}</div>}
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button
              onClick={create}
              disabled={!name || !type || isCreating}
              className="btn-primary"
              style={{ flex: 1, justifyContent: 'center', padding: '11px', opacity: !name || !type || isCreating ? 0.5 : 1, cursor: !name || !type || isCreating ? 'not-allowed' : 'pointer' }}
            >
              {isCreating ? 'Creating...' : 'Create Project'}
            </button>
            <button onClick={() => navigate(-1)} className="btn-secondary" style={{ padding: '11px 18px' }} disabled={isCreating}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
