import { NavLink, useNavigate } from 'react-router';
import { useState } from 'react';
import { useProjectContext } from '../../context/ProjectContext';

const NAV_GROUPS = [
  {
    items: [
      { to: '/workbench', label: 'ChatBench', icon: <ChatIcon /> },
      { to: '/workbench/models', label: 'Models', icon: <CpuIcon /> },
      { to: '/workbench/chat-history', label: 'Chat History', icon: <HistoryIcon /> },
    ]
  },
  {
    items: [
      { to: '/workbench/tuffy', label: 'Tuffy', icon: <TuffyIcon /> },
      { to: '/workbench/documents', label: 'Document Library', icon: <DocIcon /> },
      { to: '/workbench/runs', label: 'Agent Run History', icon: <RunIcon /> },
    ]
  },
  {
    items: [
      { to: '/workbench/security', label: 'Security', icon: <ShieldIcon /> },
      { to: '/workbench/tools', label: 'Tools', icon: <ToolIcon /> },
      { to: '/workbench/approvals', label: 'Approval Notes', icon: <NoteIcon /> },
    ]
  }
];

export function Sidebar({ collapsed, onToggle }: { collapsed?: boolean; onToggle?: () => void }) {
  const navigate = useNavigate();
  const { activeProject } = useProjectContext();
  return (
    <aside
      style={{
        width: collapsed ? 56 : 240,
        minWidth: collapsed ? 56 : 240,
        background: 'var(--surface-1)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        transition: 'width 0.22s cubic-bezier(0.4,0,0.2,1)',
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{ padding: '18px 14px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8, flexShrink: 0,
          background: 'linear-gradient(135deg, #7C3AED 0%, #0F766E 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        {!collapsed && (
          <div>
            <div className="font-display" style={{ fontSize: 14, fontWeight: 700, color: 'var(--foreground)', lineHeight: 1.2 }}>Builder AI</div>
            <div style={{ fontSize: 10, color: 'var(--muted-foreground)', fontFamily: 'JetBrains Mono', letterSpacing: '0.08em' }}>SOVEREIGN WORKBENCH</div>
          </div>
        )}
        <div style={{ flex: 1 }} />
        {!collapsed && onToggle && (
          <button onClick={onToggle} className="btn-ghost" style={{ padding: '4px 6px' }}>
            <CollapseIcon />
          </button>
        )}
      </div>

      {/* New Project */}
      <div style={{ padding: '12px 10px 8px' }}>
        <button
          onClick={() => navigate('/workbench/new-project')}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 8,
            padding: collapsed ? '8px 0' : '8px 12px',
            justifyContent: collapsed ? 'center' : 'flex-start',
            background: 'var(--violet-dim)', color: '#A78BFA',
            border: '1px solid rgba(124,58,237,0.25)', borderRadius: 7,
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
            transition: 'all 0.2s', fontFamily: 'Outfit, sans-serif',
          }}
        >
          <span style={{ fontSize: 16, lineHeight: 1 }}>+</span>
          {!collapsed && <span>New Project</span>}
        </button>
      </div>

      {/* Nav groups */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '4px 10px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {gi > 0 && <div className="divider" style={{ margin: '6px 2px' }} />}
            {group.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/workbench'}
                style={{ textDecoration: 'none' }}
              >
                {({ isActive }) => (
                  <div
                    className="sidebar-item"
                    style={{
                      justifyContent: collapsed ? 'center' : undefined,
                      padding: collapsed ? '8px 0' : undefined,
                      ...(isActive ? {
                        background: 'var(--violet-dim)',
                        color: '#A78BFA',
                        border: '1px solid rgba(124,58,237,0.2)',
                      } : {})
                    }}
                  >
                    <span style={{ flexShrink: 0, opacity: isActive ? 1 : 0.65 }}>{item.icon}</span>
                    {!collapsed && <span>{item.label}</span>}
                  </div>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: '10px 10px 14px', borderTop: '1px solid var(--border)' }}>
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'linear-gradient(135deg, #7C3AED, #0F766E)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700, color: 'white', fontFamily: 'Outfit'
            }}>B</div>
            <div>
              <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--foreground)' }}>
                {activeProject ? activeProject.name : 'No Project'}
              </div>
              <div style={{ fontSize: 10.5, color: 'var(--muted-foreground)' }}>Local Instance</div>
            </div>
          </div>
        )}
        {collapsed && (
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'linear-gradient(135deg, #7C3AED, #0F766E)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700, color: 'white'
            }}>B</div>
          </div>
        )}
      </div>
    </aside>
  );
}

function ChatIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
}
function CpuIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/></svg>;
}
function HistoryIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>;
}
function TuffyIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M22 2 12 12"/><circle cx="12" cy="12" r="3"/></svg>;
}
function DocIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>;
}
function RunIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>;
}
function ShieldIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
}
function ToolIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
}
function NoteIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>;
}
function CollapseIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>;
}
