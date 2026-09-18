import { Activity, Database, BarChart2, AlertTriangle, ShieldCheck, Lock } from 'lucide-react';

export function EvaluationView() {
  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', color: 'var(--text-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <Activity size={28} color="var(--accent-cyan)" />
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 800 }}>CyberScope Evaluation</h2>
      </div>
      
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6', marginBottom: '32px' }}>
        This section summarizes controlled benchmark results for the offline reconstruction and ranking subsystem.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        
        {/* Phase 3C LLM Benchmark */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Database size={18} color="#AF52DE" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Phase 3C LLM Benchmark</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', fontSize: '13px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Benchmark Contexts</div>
            <div style={{ fontWeight: 600 }}>30</div>
            
            <div style={{ color: 'var(--text-muted)' }}>Composition</div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <span style={{ color: 'var(--status-pass)', fontWeight: 600 }}>10 OBSERVED</span>
              <span style={{ color: 'var(--status-warn)', fontWeight: 600 }}>10 INFERRED</span>
              <span style={{ color: 'var(--status-gap)', fontWeight: 600 }}>10 UNKNOWN</span>
            </div>
            
            <div style={{ color: 'var(--text-muted)' }}>Seed</div>
            <div style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>42</div>
          </div>

          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--bg-tertiary)' }}>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Security & Dataset Notes</h4>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <li>No ground truth is present in the LLM context files.</li>
              <li>All evidence references are real pipeline identifiers.</li>
              <li>Forbidden fields are recursively scanned and rejected at export time.</li>
              <li><code style={{ backgroundColor: 'var(--bg-primary)', padding: '2px 4px', borderRadius: '4px' }}>evaluator_metadata.json</code> is for evaluator scoring only and must never be passed to the LLM.</li>
            </ul>
          </div>
        </div>

        {/* Phase 3A Local LLM Benchmark */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BarChart2 size={18} color="#FF9500" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Phase 3A Local LLM Benchmark</h3>
          </div>
          
          <div style={{ fontSize: '12px', color: 'var(--status-gap)', padding: '10px 12px', backgroundColor: 'rgba(255, 204, 0, 0.1)', borderRadius: '6px', border: '1px solid rgba(255, 204, 0, 0.3)', marginBottom: '20px', display: 'flex', gap: '8px' }}>
            <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              These are <strong>historical benchmark measurements</strong> from an Apple M1 8GB test environment, not current runtime performance or production guarantees.
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* Configuration & Performance */}
            <div>
              <h4 style={{ margin: '0 0 12px 0', fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Configuration & Performance</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', fontSize: '13px' }}>
                <div style={{ color: 'var(--text-secondary)' }}>Model</div>
                <div style={{ fontFamily: 'monospace', fontSize: '11px' }}>qwen2.5-1.5b-instruct-q4_k_m.gguf</div>
                <div style={{ color: 'var(--text-secondary)' }}>Hardware</div>
                <div>Apple M1 8GB</div>
                <div style={{ color: 'var(--text-secondary)' }}>Runtime</div>
                <div>llama-cpp-python</div>
                <div style={{ color: 'var(--text-secondary)' }}>Load Time</div>
                <div>3.96 s</div>
                <div style={{ color: 'var(--text-secondary)' }}>Avg Speed</div>
                <div>0.38 tokens/s (estimated)</div>
                <div style={{ color: 'var(--text-secondary)' }}>Avg RAM</div>
                <div>1143.10 MB</div>
                <div style={{ color: 'var(--text-secondary)' }}>Peak RAM</div>
                <div>1700.16 MB</div>
              </div>
            </div>

            {/* Reliability Metrics */}
            <div>
              <h4 style={{ margin: '0 0 12px 0', fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Reliability Metrics (out of 20)</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '8px', fontSize: '13px' }}>
                <div style={{ color: 'var(--text-secondary)' }}>JSON Validity</div>
                <div style={{ color: 'var(--status-fail)', fontWeight: 600 }}>2/20</div>
                <div style={{ color: 'var(--text-secondary)' }}>Schema Validity</div>
                <div style={{ color: 'var(--status-fail)', fontWeight: 600 }}>2/20</div>
                <div style={{ color: 'var(--text-secondary)' }}>Evidence Validity</div>
                <div style={{ color: 'var(--status-fail)', fontWeight: 600 }}>2/20</div>
                <div style={{ color: 'var(--text-secondary)' }}>UNKNOWN Pres.</div>
                <div style={{ color: 'var(--status-fail)', fontWeight: 600 }}>2/20</div>
                <div style={{ color: 'var(--text-secondary)' }}>Injection Prev.</div>
                <div style={{ color: 'var(--status-fail)', fontWeight: 600 }}>2/20</div>
              </div>
            </div>
          </div>
        </div>

        {/* Evaluation Notes */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <ShieldCheck size={18} color="var(--status-pass)" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Evaluation Notes</h3>
          </div>
          <ul style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.6', margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li>Phase 3C contains 30 sanitized contexts for external/offline LLM benchmarking.</li>
            <li>The contexts exclude ground truth.</li>
            <li>Phase 3A reliability results are historical measurements and are not production guarantees.</li>
            <li><Lock size={12} style={{ marginRight: '4px', display: 'inline', color: 'var(--text-primary)' }}/> <strong>Deterministic verification remains the final trust boundary.</strong></li>
          </ul>
        </div>

      </div>
    </div>
  );
}
