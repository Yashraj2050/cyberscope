interface ParametersPanelProps {
  rankerMode: string;
  setRankerMode: (m: string) => void;
  hybridAlpha: number;
  setHybridAlpha: (a: number) => void;
}

export function ParametersPanel({ rankerMode, setRankerMode, hybridAlpha, setHybridAlpha }: ParametersPanelProps) {
  return (
    <div className="inspector-section">
      <div className="section-title">ANALYSIS PARAMETERS</div>
      <div style={{ padding: '0 24px 24px 24px', fontSize: '12px' }}>
        
        <div style={{ marginBottom: '16px' }}>
          <div style={{ color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>Ranking Mode</div>
          <select 
            value={rankerMode} 
            onChange={(e) => setRankerMode(e.target.value)}
            style={{ width: '100%', padding: '6px', borderRadius: '4px', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--bg-tertiary)', marginBottom: '8px' }}
          >
            <option value="DETERMINISTIC">Deterministic</option>
            <option value="ML">ML</option>
            <option value="HYBRID">Hybrid</option>
          </select>
          {rankerMode === 'ML' && (
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontStyle: 'italic', marginBottom: '8px' }}>
              Local ML ranker prioritizes candidates using learned contextual features. Ranking signal only — final classification is determined by evidence verification.
            </div>
          )}
          {rankerMode === 'HYBRID' && (
            <>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontStyle: 'italic', marginBottom: '8px' }}>
                Combines deterministic baseline with ML ranking signal. Ranking signal only — final classification is determined by evidence verification.
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <label style={{ fontSize: '11px' }}>Deterministic Weight (Alpha)</label>
                <span className="mono" style={{ fontSize: '11px' }}>{hybridAlpha.toFixed(2)}</span>
              </div>
              <input 
                type="range" 
                min="0" max="1" step="0.05" 
                value={hybridAlpha}
                onChange={(e) => setHybridAlpha(parseFloat(e.target.value))}
                style={{ width: '100%', marginBottom: '8px' }}
              />
            </>
          )}
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--bg-tertiary)', margin: '16px 0' }} />

        <div style={{ marginBottom: '16px' }}>
          <div style={{ color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Gap Detection Threshold</div>
          <div className="mono">0.40</div>
        </div>
        
        <div style={{ color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Gap Signals</div>
        <div className="signal-matrix">
          <div className="matrix-row"><span>Technique Transition</span><span className="mono">HIGH</span></div>
          <div className="matrix-row"><span>Behavioral Prerequisite</span><span className="mono">HIGH</span></div>
          <div className="matrix-row"><span>Host</span><span className="mono">MED</span></div>
          <div className="matrix-row"><span>User</span><span className="mono">MED</span></div>
          <div className="matrix-row"><span>Process</span><span className="mono">MED</span></div>
          <div className="matrix-row"><span>Temporal</span><span className="mono">LOW</span></div>
        </div>
      </div>
    </div>
  );
}
