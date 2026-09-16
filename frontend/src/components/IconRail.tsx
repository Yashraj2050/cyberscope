import { Activity, GitMerge, FileSearch, ShieldAlert, CheckCircle, Settings } from 'lucide-react';

interface IconRailProps {
  activeView: string;
  onSelectView: (view: string) => void;
}

export function IconRail({ activeView, onSelectView }: IconRailProps) {
  return (
    <nav className="icon-rail">
      <button 
        className={`rail-btn ${activeView === 'Overview' ? 'active' : ''}`} 
        title="Overview"
        onClick={() => onSelectView('Overview')}
      >
        <Activity size={18} />
      </button>
      <button 
        className={`rail-btn ${activeView === 'Attack Path' ? 'active' : ''}`} 
        title="Attack Path"
        onClick={() => onSelectView('Attack Path')}
      >
        <GitMerge size={18} />
      </button>
      <button 
        className={`rail-btn ${activeView === 'Evidence' ? 'active' : ''}`} 
        title="Evidence"
        onClick={() => onSelectView('Evidence')}
      >
        <FileSearch size={18} />
      </button>
      <button 
        className={`rail-btn ${activeView === 'Candidates' ? 'active' : ''}`} 
        title="Candidates"
        onClick={() => onSelectView('Candidates')}
      >
        <ShieldAlert size={18} />
      </button>
      <button 
        className={`rail-btn ${activeView === 'Verification' ? 'active' : ''}`} 
        title="Verification"
        onClick={() => onSelectView('Verification')}
      >
        <CheckCircle size={18} />
      </button>
      
      <div style={{ flexGrow: 1 }}></div>
      
      <button 
        className={`rail-btn ${activeView === 'Engine Settings' ? 'active' : ''}`} 
        title="Engine Settings"
        onClick={() => onSelectView('Engine Settings')}
      >
        <Settings size={18} />
      </button>
    </nav>
  );
}
