import { useState, useEffect } from 'react';
import { getLlmStatus } from '../services/api';
import { Settings, Shield, Network, Cpu, BrainCircuit, Lock } from 'lucide-react';

export function SettingsView() {
  const [llmStatus, setLlmStatus] = useState<any>(null);

  useEffect(() => {
    getLlmStatus()
      .then(setLlmStatus)
      .catch(() => setLlmStatus({ provider: 'NOT CONFIGURED', active: false }));
  }, []);

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', color: 'var(--text-primary)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
        <Settings size={28} color="var(--text-muted)" />
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 800 }}>CyberScope Settings</h2>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        
        {/* Runtime Settings */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Cpu size={18} color="var(--accent-cyan)" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Runtime</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', fontSize: '13px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Engine</div>
            <div style={{ fontWeight: 600 }}>LOCAL</div>
            
            <div style={{ color: 'var(--text-muted)' }}>Network</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <Network size={14} color="var(--status-pass)" /> OFFLINE
            </div>
            
            <div style={{ color: 'var(--text-muted)' }}>Application Version</div>
            <div>Not available</div>
          </div>
        </div>

        {/* Reconstruction Settings */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BrainCircuit size={18} color="#AF52DE" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Reconstruction Pipeline</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', fontSize: '13px', marginBottom: '16px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Ranking Mode</div>
            <div>Not available</div>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', padding: '12px', backgroundColor: 'var(--bg-primary)', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
            <strong>Note:</strong> Deterministic scoring remains permanently available as the fallback and trust-preserving path.
          </div>
        </div>

        {/* Local AI Settings */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BrainCircuit size={18} color="#FF9500" />
            <h3 style={{ margin: 0, fontSize: '16px' }}>Local AI Analyst</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', fontSize: '13px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Provider Status</div>
            <div>
              {llmStatus ? (
                <span style={{ 
                  backgroundColor: llmStatus.active ? 'rgba(52, 199, 89, 0.1)' : 'rgba(255, 59, 48, 0.1)', 
                  color: llmStatus.active ? 'var(--status-pass)' : 'var(--status-fail)', 
                  padding: '2px 8px', borderRadius: '4px', fontWeight: 600, fontSize: '11px' 
                }}>
                  {llmStatus.provider || 'NOT CONFIGURED'}
                </span>
              ) : (
                <span style={{ color: 'var(--text-muted)' }}>Checking...</span>
              )}
            </div>
            
            <div style={{ color: 'var(--text-muted)' }}>Model Name</div>
            <div style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
              {llmStatus?.model || 'Not configured'}
            </div>
          </div>
        </div>

        {/* Safety Boundaries */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', padding: '24px', border: '1px solid var(--status-gap)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Shield size={18} color="var(--status-gap)" />
            <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--status-gap)' }}>Safety & Trust Boundaries</h3>
          </div>
          
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <li><Lock size={12} style={{ marginRight: '6px', display: 'inline' }}/> <strong>Deterministic Verification</strong> remains the final trust boundary of the system.</li>
            <li><Lock size={12} style={{ marginRight: '6px', display: 'inline' }}/> The local LLM cannot create evidence, invent telemetry, or override verification results.</li>
            <li><Lock size={12} style={{ marginRight: '6px', display: 'inline' }}/> <strong>UNKNOWN</strong> status must remain UNKNOWN when deterministic verification does not establish the transition.</li>
          </ul>
        </div>

      </div>
    </div>
  );
}
