import { Link } from 'react-router-dom';
import { Database, Plus, Search } from 'lucide-react';

export function CasesList() {
  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Database size={24} /> Investigation Cases
        </h1>
        <button className="btn btn-primary">
          <Plus size={16} /> NEW CASE
        </button>
      </div>

      <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--bg-tertiary)', display: 'flex', gap: '16px' }}>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', backgroundColor: 'var(--bg-primary)', padding: '8px 12px', borderRadius: '4px', border: '1px solid var(--bg-tertiary)' }}>
            <Search size={14} style={{ color: 'var(--text-muted)', marginRight: '8px' }} />
            <input type="text" placeholder="Search cases..." style={{ border: 'none', backgroundColor: 'transparent', color: 'var(--text-primary)', outline: 'none', width: '100%' }} />
          </div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--bg-tertiary)', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>CASE ID</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>TITLE</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>LAST UPDATED</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--bg-tertiary)', cursor: 'pointer' }}>
              <td style={{ padding: '12px 16px' }}>
                <Link to="/cases/scenario_001.json" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 600 }}>
                  CASE-2026-001
                </Link>
              </td>
              <td style={{ padding: '12px 16px' }}>Suspicious Lateral Movement via SMB</td>
              <td style={{ padding: '12px 16px' }}>
                <span style={{ padding: '2px 8px', backgroundColor: 'rgba(234, 179, 8, 0.1)', color: '#eab308', borderRadius: '999px', fontSize: '12px', fontWeight: 600 }}>OPEN</span>
              </td>
              <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Just now</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
