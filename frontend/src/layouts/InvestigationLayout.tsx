import { Outlet, useParams, Link, useLocation } from 'react-router-dom';
import { Network, Activity, List, Download, Search, FileText, CheckCircle, Zap } from 'lucide-react';

export function InvestigationLayout() {
  const { caseId } = useParams();
  const location = useLocation();

  const navItems = [
    { path: `/cases/${caseId}`, label: 'Overview', icon: <Search size={14} /> },
    { path: `/cases/${caseId}/timeline`, label: 'Timeline', icon: <Activity size={14} /> },
    { path: `/cases/${caseId}/graph`, label: 'Attack Graph', icon: <Network size={14} /> },
    { path: `/cases/${caseId}/telemetry`, label: 'Telemetry', icon: <List size={14} /> },
    { path: `/cases/${caseId}/gaps`, label: 'Gaps', icon: <Search size={14} /> },
    { path: `/cases/${caseId}/candidates`, label: 'Candidates', icon: <List size={14} /> },
    { path: `/cases/${caseId}/evidence`, label: 'Evidence', icon: <FileText size={14} /> },
    { path: `/cases/${caseId}/verification`, label: 'Verification', icon: <CheckCircle size={14} /> },
    { path: `/cases/${caseId}/ai`, label: 'AI Analyst', icon: <Zap size={14} /> },
    { path: `/cases/${caseId}/report`, label: 'Reports', icon: <Download size={14} /> }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* INVESTIGATION HEADER */}
      <header className="topbar" style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 24px' }}>
        <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>CYBERSCOPE</span>
          <span style={{ color: 'var(--text-muted)' }}>|</span>
          <span style={{ color: 'var(--color-primary)' }}>{caseId || 'CASE-2026-001'}</span>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', fontWeight: 600 }}>
          <span style={{ color: 'var(--color-success)' }}>LOCAL</span> • <span>OFFLINE</span>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* INVESTIGATION SIDEBAR */}
        <aside style={{ width: '200px', backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--bg-tertiary)', padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Investigation
          </div>
          {navItems.map(item => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`btn ${location.pathname === item.path ? 'btn-primary' : ''}`}
              style={{ justifyContent: 'flex-start', padding: '8px 12px', border: 'none', backgroundColor: location.pathname === item.path ? 'var(--bg-tertiary)' : 'transparent', color: location.pathname === item.path ? 'var(--text-primary)' : 'var(--text-secondary)' }}
            >
              {item.icon} {item.label}
            </Link>
          ))}
        </aside>

        {/* INVESTIGATION CONTENT */}
        <div style={{ flex: 1, overflow: 'auto', backgroundColor: 'var(--bg-primary)' }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
