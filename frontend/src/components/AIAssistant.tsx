import { useState, useEffect } from 'react';

interface AIAssistantProps {
  caseId: string;
  decision: string;
  evidenceStrength: string;
}

interface LLMResponse {
  summary: string;
  assessment: string;
  evidence_references: string[];
  candidate_discussion: string[];
  uncertainty: string;
  recommended_next_checks: string[];
}

export function AIAssistant({ caseId, decision, evidenceStrength }: AIAssistantProps) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [explanation, setExplanation] = useState<LLMResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/llm/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(err => console.error("Failed to fetch LLM status", err));
  }, []);

  const handleExplain = async () => {
    if (loading) return;
    setLoading(true);
    setErrorMsg(null);
    setExplanation(null);

    try {
      const res = await fetch(`/api/v1/investigations/${caseId}/ai/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        setErrorMsg(data.detail || 'An error occurred.');
      } else {
        setExplanation(data);
      }
    } catch (err) {
      setErrorMsg('Failed to contact local assistant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)', borderLeft: '1px solid var(--bg-tertiary)', width: '350px' }}>
      
      {/* Header */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--bg-tertiary)', backgroundColor: 'var(--bg-secondary)' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>CyberScope Investigation Assistant</div>
        <div style={{ display: 'flex', gap: '8px', fontSize: '10px', flexWrap: 'wrap' }}>
          <span className="badge badge-neutral">LOCAL MODEL</span>
          <span className="badge badge-neutral">EVIDENCE-GROUNDED</span>
          <span className="badge badge-neutral">VERIFIER-AUTHORITATIVE</span>
        </div>
        
        {status && !status.available && (
          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-danger)', padding: '6px', backgroundColor: 'rgba(255,0,0,0.1)', borderRadius: '4px' }}>
            LLM_UNAVAILABLE: Configured model is missing or invalid.
          </div>
        )}
        
        <div style={{ marginTop: '12px', fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
          <span>Investigation: <strong>{caseId}</strong></span>
        </div>
        <div style={{ marginTop: '4px', fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
          <span>Decision: <strong className={`status-${decision}`}>{decision}</strong></span>
          <span>Strength: <strong>{evidenceStrength}</strong></span>
        </div>
      </div>

      {/* Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        <div style={{ fontSize: '11px', fontStyle: 'italic', color: 'var(--text-muted)', borderLeft: '2px solid var(--accent-primary)', paddingLeft: '8px' }}>
          AI-generated advisory explanation. Final classification is determined by CyberScope's evidence verification engine.
        </div>

        {!explanation && !loading && !errorMsg && (
          <button 
            onClick={handleExplain}
            disabled={status && !status.available}
            style={{ padding: '12px 16px', borderRadius: '4px', border: '1px solid var(--bg-tertiary)', backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', cursor: (status && !status.available) ? 'not-allowed' : 'pointer', fontSize: '13px', fontWeight: 600 }}
          >
            Generate AI Explanation
          </button>
        )}

        {loading && (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Analyzing evidence package and retrieving local knowledge...
          </div>
        )}

        {errorMsg && (
          <div style={{ fontSize: '12px', color: 'var(--text-danger)', backgroundColor: 'rgba(255,0,0,0.1)', padding: '12px', borderRadius: '4px' }}>
            {errorMsg}
          </div>
        )}

        {explanation && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Summary</div>
              <div>{explanation.summary}</div>
            </div>
            
            <div>
              <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Assessment</div>
              <div>{explanation.assessment}</div>
            </div>
            
            {explanation.evidence_references && explanation.evidence_references.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Evidence Cited</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {explanation.evidence_references.map(ref => (
                    <span key={ref} style={{ fontSize: '11px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--bg-tertiary)', padding: '2px 6px', borderRadius: '4px' }}>
                      {ref}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {explanation.candidate_discussion && explanation.candidate_discussion.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Candidate Discussion</div>
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  {explanation.candidate_discussion.map((disc, i) => <li key={i}>{disc}</li>)}
                </ul>
              </div>
            )}
            
            {explanation.uncertainty && (
              <div>
                <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-warning)', textTransform: 'uppercase', marginBottom: '4px' }}>Uncertainties</div>
                <div style={{ color: 'var(--text-warning)' }}>{explanation.uncertainty}</div>
              </div>
            )}
            
            {explanation.recommended_next_checks && explanation.recommended_next_checks.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: '11px', color: 'var(--accent-primary)', textTransform: 'uppercase', marginBottom: '4px' }}>Recommended Checks</div>
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  {explanation.recommended_next_checks.map((check, i) => <li key={i}>{check}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
