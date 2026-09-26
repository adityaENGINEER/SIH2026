import { Outlet, useLocation } from 'react-router';
import { Navbar } from './Navbar';

export function Root() {
  const location = useLocation();
  const isWorkbench = location.pathname.startsWith('/workbench');

  return (
    <div style={{ minHeight: '100vh', background: 'var(--background)', display: 'flex', flexDirection: 'column' }}>
      {!isWorkbench && <Navbar />}
      <div style={{ flex: isWorkbench ? 1 : undefined, overflow: isWorkbench ? 'hidden' : undefined, height: isWorkbench ? '100vh' : undefined }}>
        <Outlet />
      </div>
    </div>
  );
}
