import { Outlet, useNavigate, useLocation, NavLink } from 'react-router';
import { Sidebar } from './Sidebar';
import { useState, useEffect } from 'react';
import { useProjectContext } from '../../context/ProjectContext';
import { projectsApi } from '../../services/projectsApi';
import { Project } from '../../services/types';

export function WorkbenchLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { activeProject, setActiveProject } = useProjectContext();
  const [projects, setProjects] = useState<Project[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);

  useEffect(() => {
    projectsApi.list().then(data => {
      setBackendError(null);
      setProjects(data);
      if (data.length > 0) {
        // If there's an active project in context, verify it exists. If not, pick the first one.
        if (!activeProject || !data.find(p => p.project_id === activeProject.project_id)) {
          setActiveProject(data[0]);
        }
      } else {
        // No projects exist, maybe clear active project
        setActiveProject(null);
      }
    }).catch(err => setBackendError(err instanceof TypeError ? 'Backend unavailable' : `Projects failed to load: ${err.message}`));
  }, [activeProject?.project_id, setActiveProject, retryToken]);

  const currentPage = getPageLabel(location.pathname);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--background)' }}>
      {/* Desktop sidebar */}
      <div className="workbench-sidebar">
        <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(c => !c)} />
      </div>

      {/* Mobile overlay */}
      {mobileDrawerOpen && (
        <div
          onClick={() => setMobileDrawerOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 40 }}
        />
      )}

      {/* Mobile drawer */}
      <div style={{
        position: 'fixed', top: 0, left: 0, bottom: 0,
        width: 260, zIndex: 50,
        transform: mobileDrawerOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.25s cubic-bezier(0.4,0,0.2,1)',
      }} className="workbench-mobile-drawer">
        <Sidebar />
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Top bar */}
        <div style={{
          height: 52, flexShrink: 0,
          background: 'var(--surface-1)',
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', padding: '0 20px', gap: 12
        }}>
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileDrawerOpen(true)}
            className="workbench-hamburger"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--muted-foreground)', padding: '4px 6px', borderRadius: 6,
              display: 'flex', alignItems: 'center',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          </button>

          {/* Collapse button for desktop */}
          {sidebarCollapsed && (
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="btn-ghost workbench-desktop-only"
              style={{ padding: '4px 8px' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono' }}>WORKBENCH</span>
            <span style={{ color: 'var(--border)' }}>/</span>
            <span className="font-display" style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>{currentPage}</span>
          </div>

          <div style={{ flex: 1 }} />

          <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {backendError && (
              <button className="badge badge-red" style={{ fontSize: 10.5, marginRight: 6, cursor: 'pointer', border: 'none' }}
                title="Retry" onClick={() => setRetryToken(t => t + 1)}>
                {backendError} · retry
              </button>
            )}
            <span className="badge badge-green" style={{ fontSize: 10.5 }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
              Local
            </span>
            <select 
              value={activeProject?.project_id || ''}
              onChange={(e) => {
                const p = projects.find(proj => proj.project_id === e.target.value);
                if (p) setActiveProject(p);
              }}
              style={{
                fontSize: 11.5,
                color: 'var(--muted-foreground)',
                fontFamily: 'JetBrains Mono',
                marginLeft: 8,
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 4,
                padding: '2px 4px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="" disabled>Select Project</option>
              {projects.map(p => (
                <option key={p.project_id} value={p.project_id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Outlet />
        </div>

        {/* Mobile bottom nav */}
        <div className="workbench-bottom-nav" style={{
          borderTop: '1px solid var(--border)',
          background: 'var(--surface-1)',
          display: 'flex',
          padding: '6px 8px',
        }}>
          {[
            { to: '/workbench', label: 'Chat', icon: '💬' },
            { to: '/workbench/tuffy', label: 'Tuffy', icon: '⚙️' },
            { to: '/workbench/documents', label: 'Docs', icon: '📄' },
            { to: '/workbench/runs', label: 'Runs', icon: '▶️' },
            { to: '/workbench/security', label: 'More', icon: '⋯' },
          ].map(item => (
            <NavLink key={item.to} to={item.to} end={item.to === '/workbench'} style={{ flex: 1, textDecoration: 'none' }}>
              {({ isActive }) => (
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                  padding: '6px 4px', borderRadius: 8,
                  background: isActive ? 'var(--violet-dim)' : 'transparent',
                  color: isActive ? '#A78BFA' : 'var(--muted-foreground)',
                }}>
                  <span style={{ fontSize: 16 }}>{item.icon}</span>
                  <span style={{ fontSize: 10, fontWeight: 600 }}>{item.label}</span>
                </div>
              )}
            </NavLink>
          ))}
        </div>
      </div>

      <style>{`
        @media (min-width: 769px) {
          .workbench-sidebar { display: flex; }
          .workbench-hamburger { display: none !important; }
          .workbench-bottom-nav { display: none !important; }
          .workbench-mobile-drawer { display: none !important; }
        }
        @media (max-width: 768px) {
          .workbench-sidebar { display: none; }
          .workbench-desktop-only { display: none !important; }
          .workbench-bottom-nav { display: flex; }
        }
      `}</style>
    </div>
  );
}

function getPageLabel(path: string): string {
  const map: Record<string, string> = {
    '/workbench': 'ChatBench',
    '/workbench/models': 'Models',
    '/workbench/chat-history': 'Chat History',
    '/workbench/tuffy': 'Tuffy',
    '/workbench/documents': 'Document Library',
    '/workbench/runs': 'Agent Run History',
    '/workbench/security': 'Security',
    '/workbench/tools': 'Tools',
    '/workbench/approvals': 'Approval Notes',
    '/workbench/new-project': 'New Project',
  };
  return map[path] || 'Workbench';
}
