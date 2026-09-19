import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { type FullPipelineResult, runAnalysis } from '../services/api';

export function ReportsView() {
  const { caseId } = useParams();
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';

  useEffect(() => {
    setLoading(true);
    runAnalysis(scenarioId)
      .then(res => {
        if (res && res.length > 0) {
          setPipelineResult(res[0]);
        } else {
          setError("No report data found.");
        }
      })
      .catch(err => setError(err.message || 'Failed to fetch report data'))
      .finally(() => setLoading(false));
  }, [scenarioId]);

  if (loading) {
    return (
      <div style={{ padding: '40px', color: 'var(--text-muted)' }}>
        Loading investigation report...
      </div>
    );
  }

  if (error || !pipelineResult) {
    return (
      <div style={{ padding: '40px', color: 'var(--status-fail)' }}>
        Error: {error || 'No report data.'}
      </div>
    );
  }

  const { gap, candidates, result, analysis_metadata } = pipelineResult;

  const exportReport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(pipelineResult, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `Report_${scenarioId.replace('.json', '')}_${new Date().getTime()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OBSERVED':
      case 'INFERRED': return 'var(--status-pass)';
      case 'UNKNOWN': return 'var(--status-gap)';
      default: return 'var(--text-primary)';
    }
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: 'calc(100vh - 48px)', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* Header & Export Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0' }}>Supervisory Assessment Report</h2>
          <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
            Case: {scenarioId} • {analysis_metadata?.ml_inference_timestamp || new Date().toISOString()}
          </div>
        </div>
        <button
          onClick={exportReport}
          style={{
            backgroundColor: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            padding: '8px 16px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Export Report (JSON)
        </button>
      </div>

      {/* Integrity Notice */}
      <div style={{ backgroundColor: 'rgba(100, 210, 255, 0.05)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(100, 210, 255, 0.2)' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '8px', textTransform: 'uppercase' }}>
          Report Integrity
        </div>
        <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <li>Analysis generated locally — supports offline supervisory assessment.</li>
          <li>Evidence references come exclusively from observed operational telemetry.</li>
          <li>Final classification is strictly determined by the deterministic verification engine.</li>
          <li>AI Analyst (if used) provides explanation only and does not alter the final decision.</li>
        </ul>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* EXECUTIVE SUMMARY */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-primary)' }}>EXECUTIVE SUMMARY</h3>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Final Classification</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: getStatusColor(result.status) }}>
              {result.status}
            </div>
            {result.status === 'UNKNOWN' && (
              <>
                <div style={{ fontSize: '13px', color: 'var(--status-gap)', marginTop: '8px', fontWeight: 600 }}>
                  Evidence insufficient to establish the missing event.
                </div>
                <div style={{ fontSize: '11px', color: 'var(--status-gap)', marginTop: '6px', padding: '6px 10px', backgroundColor: 'rgba(255, 159, 10, 0.08)', borderRadius: '4px', fontWeight: 600 }}>
                  SUPERVISORY REVIEW: REQUIRED
                </div>
              </>
            )}
            {result.status === 'INFERRED' && (
              <div style={{ fontSize: '13px', color: 'var(--status-pass)', marginTop: '8px' }}>
                Event reconstructed from supporting evidence (not directly observed).
              </div>
            )}
            {result.status === 'OBSERVED' && (
              <div style={{ fontSize: '13px', color: 'var(--accent-cyan)', marginTop: '8px' }}>
                Direct observed telemetry reference verified.
              </div>
            )}
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Analyst Explanation</div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {result.explanation}
            </div>
          </div>
        </div>

        {/* GAP ANALYSIS */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-primary)' }}>EVIDENCE GAP ANALYSIS</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Gap ID</div>
              <div style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{gap.gap_id.split('-')[0]}...</div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Score</div>
              <div style={{ fontSize: '13px', fontWeight: 700 }}>{gap.gap_score.toFixed(2)}</div>
            </div>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Detection Signals</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            {Object.entries(gap.detection_signals).map(([key, val]) => (
              <div key={key} style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between', padding: '4px 8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-muted)' }}>{key.replace('_', ' ')}</span>
                <span style={{ color: val ? 'var(--status-fail)' : 'var(--text-primary)' }}>{val ? 'TRUE' : 'FALSE'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CANDIDATE ANALYSIS */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-primary)' }}>CANDIDATE ANALYSIS</h3>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Ranker Mode: {analysis_metadata?.ranker_mode || 'UNKNOWN'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {candidates.map((c) => (
              <div key={c.candidate_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
                    {c.rank}
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.technique_id}</div>
                </div>
                <div style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{c.final_ranking_score.toFixed(4)}</div>
              </div>
            ))}
          </div>
        </div>

        {/* VERIFICATION */}
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-primary)' }}>VERIFICATION CHECKS</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Candidate Score</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{result.candidate_score?.toFixed(4) || 'N/A'}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Verification Score</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{result.verification_score.toFixed(4)}</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {Object.entries(result.verification_checks).map(([check, status]) => (
              <div key={check} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', padding: '6px 12px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-primary)' }}>{check}</span>
                <span style={{ fontWeight: 700, color: status === 'PASS' ? 'var(--status-pass)' : status === 'FAIL' ? 'var(--status-fail)' : 'var(--status-gap)' }}>{status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* EVIDENCE TRACE */}
        <div style={{ gridColumn: '1 / -1', backgroundColor: 'var(--bg-secondary)', padding: '20px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-primary)' }}>EVIDENCE TRACE</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--status-pass)', marginBottom: '8px' }}>Supporting Evidence</div>
              {result.supporting_evidence.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {result.supporting_evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                </ul>
              ) : <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None</div>}
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--status-fail)', marginBottom: '8px' }}>Contradictory Evidence</div>
              {result.contradictory_evidence.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '13px', color: 'var(--status-fail)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {result.contradictory_evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                </ul>
              ) : <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None</div>}
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--status-gap)', marginBottom: '8px' }}>Missing Evidence</div>
              {result.missing_evidence.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {result.missing_evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                </ul>
              ) : <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None</div>}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
