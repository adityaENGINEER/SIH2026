import { Link, NavLink, useNavigate } from 'react-router';
import { useState } from 'react';

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 50,
      background: 'rgba(10,10,15,0.92)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{ maxWidth: 1440, margin: '0 auto', padding: '0 32px', display: 'flex', alignItems: 'center', height: 58 }}>
        {/* Logo */}
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 7,
            background: 'linear-gradient(135deg, #7C3AED 0%, #0F766E 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L3 7l9 5 9-5-9-5zM3 17l9 5 9-5M3 12l9 5 9-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="font-display" style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)' }}>Builder AI</span>
        </Link>

        {/* Center nav — desktop */}
        <nav style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: 4 }} className="hidden-mobile">
          {[
            { to: '/', label: 'Home' },
            { to: '/workbench', label: 'Workbench' },
            { to: '/about', label: 'About' },
            { to: '/services', label: 'Services' },
          ].map(link => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} style={{ textDecoration: 'none' }}>
              {({ isActive }) => (
                <span style={{
                  padding: '6px 16px',
                  borderRadius: 6,
                  fontSize: 13.5,
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--foreground)' : 'var(--muted-foreground)',
                  background: isActive ? 'var(--surface-2)' : 'transparent',
                  transition: 'all 0.15s',
                  cursor: 'pointer',
                  display: 'block',
                }}>
                  {link.label}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div style={{ flex: 1 }} className="show-mobile" />

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => navigate('/workbench')}
            className="btn-primary hidden-mobile"
            style={{ padding: '7px 18px', fontSize: 13 }}
          >
            Get Started
          </button>
          {/* Hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="btn-ghost show-mobile"
            style={{ padding: '6px 8px' }}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div style={{
          padding: '12px 20px 20px',
          borderTop: '1px solid var(--border)',
          background: 'rgba(10,10,15,0.98)',
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
        }} className="show-mobile">
          {[
            { to: '/', label: 'Home' },
            { to: '/workbench', label: 'Workbench' },
            { to: '/about', label: 'About' },
            { to: '/services', label: 'Services' },
          ].map(link => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} style={{ textDecoration: 'none' }} onClick={() => setMobileMenuOpen(false)}>
              {({ isActive }) => (
                <div style={{
                  padding: '11px 14px', borderRadius: 8, fontSize: 15, fontWeight: 600,
                  color: isActive ? '#A78BFA' : 'var(--foreground)',
                  background: isActive ? 'var(--violet-dim)' : 'transparent',
                }}>
                  {link.label}
                </div>
              )}
            </NavLink>
          ))}
          <button
            onClick={() => { navigate('/workbench'); setMobileMenuOpen(false); }}
            className="btn-primary"
            style={{ marginTop: 8 }}
          >
            Get Started
          </button>
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .hidden-mobile { display: none !important; }
        }
        @media (min-width: 769px) {
          .show-mobile { display: none !important; }
        }
      `}</style>
    </header>
  );
}
