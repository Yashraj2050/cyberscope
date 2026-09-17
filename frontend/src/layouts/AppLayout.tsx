import { Outlet, Link, useLocation } from 'react-router-dom';
import { Database, Settings, Activity } from 'lucide-react';

export function AppLayout() {
  const location = useLocation();

  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* GLOBAL SIDEBAR */}
      <aside style={{ width: '250px', backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--bg-tertiary)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px', fontWeight: 800, letterSpacing: '2px', borderBottom: '1px solid var(--bg-tertiary)' }}>
          CYBERSCOPE
          <div style={{ fontSize: '10px', fontWeight: 400, color: 'var(--text-muted)', marginTop: '4px' }}>
            Security Investigation Platform
          </div>
        </div>
        
        <nav style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          <Link to="/cases" className={`btn ${location.pathname.startsWith('/cases') ? 'btn-primary' : ''}`} style={{ justifyContent: 'flex-start' }}>
            <Database size={16} /> Cases
          </Link>
          <Link to="/evaluation" className={`btn ${location.pathname.startsWith('/evaluation') ? 'btn-primary' : ''}`} style={{ justifyContent: 'flex-start' }}>
            <Activity size={16} /> Evaluation
          </Link>
          <Link to="/settings" className={`btn ${location.pathname.startsWith('/settings') ? 'btn-primary' : ''}`} style={{ justifyContent: 'flex-start' }}>
            <Settings size={16} /> Settings
          </Link>
        </nav>

        <div style={{ padding: '16px', borderTop: '1px solid var(--bg-tertiary)', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
             <div className="status-dot ready"></div> ENGINE: LOCAL
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
             <div className="status-dot ready"></div> NETWORK: OFFLINE
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Outlet />
      </main>
    </div>
  );
}
