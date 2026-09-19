import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { type FullPipelineResult, runAnalysis } from '../services/api';

function VerificationCard({ result }: { result: FullPipelineResult }) {
  const { result: verifResult } = result;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OBSERVED': return 'var(--accent-cyan)';
      case 'INFERRED': return 'var(--status-pass)';
      case 'UNKNOWN': return 'var(--status-gap)';
      case 'PASS': return 'var(--status-pass)';
      case 'FAIL': return 'var(--status-fail)';
      default: return 'var(--text-muted)';
    }
  };

  const getConfidenceColor = (label: string) => {
    switch (label) {
      case 'HIGH': return 'var(--status-pass)';
      case 'MEDIUM': return 'var(--status-gap)';
      case 'LOW': return 'var(--status-fail)';
      default: return 'var(--text-muted)';
    }
  };

  const checks = Object.entries(verifResult.verification_checks || {});
  const passedChecks = checks.filter(([_, v]) => v === 'PASS').length;
  const failedChecks = checks.filter(([_, v]) => v === 'FAIL').length;
  const unknownChecks = checks.filter(([_, v]) => v === 'UNKNOWN').length;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--bg-tertiary)',
      borderRadius: '8px',
      overflow: 'hidden',
      marginBottom: '24px',
    }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid var(--bg-tertiary)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        backgroundColor: 'var(--bg-primary)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>Final Classification</span>
          </div>
          <div style={{
            fontSize: '32px',
            fontWeight: 800,
            color: getStatusColor(verifResult.status),
            letterSpacing: '1px',
            marginBottom: '4px'
          }}>
            {verifResult.status}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {verifResult.status === 'INFERRED' && 'Event is reconstructed from supporting evidence (not directly observed).'}
            {verifResult.status === 'UNKNOWN' && 'Evidence insufficient to establish the missing event. Supervisory review required.'}
            {verifResult.status === 'OBSERVED' && 'Event was directly observed in telemetry.'}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '32px', textAlign: 'right' }}>
          <div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Candidate Score</div>
            <div style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              {verifResult.candidate_score !== null ? verifResult.candidate_score?.toFixed(4) : 'N/A'}
            </div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Evidence Support Score</div>
          </div>
          <div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Verification Score</div>
            <div style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              {verifResult.verification_score.toFixed(4)}
            </div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Evidence Support</div>
          </div>
          <div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Evidence Strength</div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: getConfidenceColor(verifResult.confidence_label) }}>
              {verifResult.confidence_label}
            </div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Confidence Label</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex' }}>

        {/* Supervisory Review Status */}
      </div>
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--bg-tertiary)',
        backgroundColor: verifResult.status === 'UNKNOWN' ? 'rgba(255, 159, 10, 0.06)' : 'rgba(52, 199, 89, 0.04)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
            Supervisory Review
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, maxWidth: '600px' }}>
            {verifResult.status === 'UNKNOWN'
              ? 'Multiple candidates remain plausible, while available telemetry does not uniquely support one reconstruction.'
              : 'The deterministic verification engine has established a classification based on available evidence.'}
          </div>
        </div>
        <span style={{
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '10px',
          fontWeight: 700,
          letterSpacing: '0.5px',
          backgroundColor: verifResult.status === 'UNKNOWN' ? 'rgba(255, 159, 10, 0.15)' : 'rgba(52, 199, 89, 0.1)',
          color: verifResult.status === 'UNKNOWN' ? 'var(--status-gap)' : 'var(--status-pass)',
        }}>
          {verifResult.status === 'UNKNOWN' ? 'REQUIRED' : 'SUPPORTED BY AVAILABLE EVIDENCE'}
        </span>
      </div>

      <div style={{ display: 'flex' }}>
        {/* Verification Checks */}
        <div style={{ flex: '2', padding: '24px', borderRight: '1px solid var(--bg-tertiary)' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', justifyContent: 'space-between' }}>
            <span>Verification Checks ({checks.length})</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 'normal' }}>
              <span style={{ color: 'var(--status-pass)' }}>{passedChecks} Pass</span> • <span style={{ color: 'var(--status-fail)' }}>{failedChecks} Fail</span> • <span style={{ color: 'var(--status-gap)' }}>{unknownChecks} Unknown</span>
            </span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {checks.map(([checkName, checkStatus], idx) => (
              <div key={idx} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '12px 16px', backgroundColor: 'var(--bg-primary)', borderRadius: '6px',
                borderLeft: `3px solid ${getStatusColor(checkStatus)}`
              }}>
                <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>{checkName}</span>
                <span style={{
                  fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
                  backgroundColor: checkStatus === 'PASS' ? 'rgba(52, 199, 89, 0.1)' : checkStatus === 'FAIL' ? 'rgba(255, 59, 48, 0.1)' : 'rgba(255, 159, 10, 0.1)',
                  color: getStatusColor(checkStatus)
                }}>
                  {checkStatus}
                </span>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', padding: '16px', backgroundColor: 'rgba(255, 159, 10, 0.05)', border: '1px solid rgba(255, 159, 10, 0.2)', borderRadius: '8px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--status-gap)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Final Explanation
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {verifResult.explanation}
            </div>
          </div>
        </div>

        {/* Evidence Trace & Decision Logic */}
        <div style={{ flex: '1.5', padding: '24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Decision Logic
            </div>
            <div style={{ backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '6px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <div style={{ marginBottom: '8px', color: 'var(--text-primary)', fontWeight: 500 }}>The verification engine enforces conservative classification rules:</div>
              <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <li><strong>Rule 1:</strong> Any FAIL check → <span style={{ color: 'var(--status-gap)' }}>UNKNOWN (veto)</span></li>
                <li><strong>Rule 2:</strong> Ambiguous top candidates (tie) → <span style={{ color: 'var(--status-gap)' }}>UNKNOWN</span></li>
                <li><strong>Rule 3:</strong> Verification score &lt; threshold → <span style={{ color: 'var(--status-gap)' }}>UNKNOWN</span></li>
                <li><strong>Rule 4:</strong> Otherwise → <span style={{ color: 'var(--status-pass)' }}>INFERRED</span></li>
              </ul>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Evidence Trace
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Supporting Evidence</div>
                {verifResult.supporting_evidence.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {verifResult.supporting_evidence.map((ev, i) => (
                      <span key={i} style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 6px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', border: '1px solid var(--bg-tertiary)' }}>{ev}</span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None found.</div>
                )}
              </div>
              
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Contradictory Evidence</div>
                {verifResult.contradictory_evidence.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {verifResult.contradictory_evidence.map((ev, i) => (
                      <span key={i} style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', padding: '2px 6px', backgroundColor: 'rgba(255, 59, 48, 0.1)', color: 'var(--status-fail)', borderRadius: '4px', border: '1px solid rgba(255, 59, 48, 0.3)' }}>{ev}</span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None found.</div>
                )}
              </div>

              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Missing Evidence</div>
                {verifResult.missing_evidence.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {verifResult.missing_evidence.map((ev, i) => (
                      <div key={i} style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>• {ev}</div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None missing.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function VerificationView() {
  const { caseId } = useParams();
  const [data, setData] = useState<FullPipelineResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';
    setLoading(true);
    setError(null);

    runAnalysis(scenarioId)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to retrieve verification data.');
        setLoading(false);
      });
  }, [caseId]);

  if (loading) {
    return (
      <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
        <div style={{
          width: '32px', height: '32px', border: '3px solid var(--bg-tertiary)',
          borderTopColor: 'var(--accent-cyan)', borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Running verification checks and evaluating evidence strength...
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px' }}>
        <div style={{
          backgroundColor: 'rgba(255, 59, 48, 0.08)',
          border: '1px solid rgba(255, 59, 48, 0.3)',
          borderRadius: '8px',
          padding: '20px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start',
        }}>
          <span style={{ color: 'var(--status-fail)', fontSize: '18px' }}>⚠</span>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--status-fail)', fontSize: '13px', marginBottom: '4px' }}>
              Verification Engine Failed
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--bg-tertiary)',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', letterSpacing: '0.5px' }}>
          Verification Engine — Supervisory Assessment Trust Boundary
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          The verification layer acts as the final arbiter for reconstruction and the trust boundary for supervisory assessment.
          A high Candidate Score indicates that an event is a likely hypothesis, but it is <strong>not</strong> a probability, 
          and it does not prove the event occurred. The Verification Score evaluates the strength of actual 
          surrounding evidence to establish the final classification. When evidence is insufficient, the system abstains
          and flags the result for human supervisory review.
        </div>
      </div>

      {data.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No verification results found for this scenario.
        </div>
      ) : (
        data.map((item, index) => (
          <div key={item.result.reconstruction_id || index}>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>
              Reconstructing Gap <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{item.gap.gap_id}</span>
              {item.result.technique_id && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> • Candidate {item.result.technique_id} ({item.result.technique_name})</span>}
            </div>
            <VerificationCard result={item} />
          </div>
        ))
      )}
    </div>
  );
}
