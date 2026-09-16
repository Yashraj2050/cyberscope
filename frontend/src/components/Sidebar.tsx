import { Home, Search, Layers, Link2, GitFork, FileText, Settings, Database } from 'lucide-react';

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
  isOffline: boolean;
}

export function Sidebar({ activeView, setActiveView, isOffline }: SidebarProps) {
  const navItems = [
    { name: 'Overview', icon: Home },
    { name: 'Scenarios', icon: Layers },
    { name: 'Investigations', icon: Search },
    { name: 'Attack Graph', icon: GitFork },
    { name: 'Reconstructions', icon: Link2 },
    { name: 'Evidence', icon: Database },
    { name: 'Reports', icon: FileText },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>CYBERSCOPE</h1>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map(item => (
          <div 
            key={item.name}
            className={`nav-item ${activeView === item.name ? 'active' : ''}`}
            onClick={() => setActiveView(item.name)}
          >
            <item.icon size={16} />
            <span>{item.name}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="engine-status">
          <div className="dot" style={{ backgroundColor: isOffline ? 'var(--status-observed)' : 'var(--text-muted)' }}></div>
          ENGINE OFFLINE
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge-outline">LOCAL</span>
          <span className="badge-outline">V0.1.0</span>
        </div>
        <div 
          className={`nav-item ${activeView === 'Settings' ? 'active' : ''}`}
          onClick={() => setActiveView('Settings')}
          style={{ padding: '8px 0', marginTop: '8px' }}
        >
          <Settings size={16} />
          <span>Settings</span>
        </div>
      </div>
    </aside>
  );
}
