import { Search } from 'lucide-react';

interface TopbarProps {
  breadcrumb: string;
  onOpenCommandPalette: () => void;
}

export function Topbar({ breadcrumb, onOpenCommandPalette }: TopbarProps) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <span>CyberScope</span>
        <span className="breadcrumb-separator">/</span>
        <span style={{ color: 'var(--text-primary)' }}>{breadcrumb}</span>
      </div>

      <div className="topbar-right">
        <button className="command-trigger" onClick={onOpenCommandPalette}>
          <Search size={14} />
          <span>Search workspaces...</span>
          <span className="command-kbd">⌘K</span>
        </button>
      </div>
    </header>
  );
}
