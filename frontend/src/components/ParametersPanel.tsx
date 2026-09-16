export function ParametersPanel() {
  return (
    <div className="inspector-section">
      <div className="section-title">ANALYSIS PARAMETERS</div>
      <div style={{ padding: '0 24px 24px 24px', fontSize: '12px' }}>
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
