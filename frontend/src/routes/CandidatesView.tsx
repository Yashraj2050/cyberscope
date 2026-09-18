import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { type GapWithCandidates, type ReconstructionCandidate, getCandidates } from '../services/api';

function CandidateCard({ candidate, isTiedTop }: { candidate: ReconstructionCandidate, isTiedTop: boolean }) {
  const formatScore = (val: number | null | undefined) => {
    if (val === null || val === undefined) return 'N/A';
    return val.toFixed(4);
  };

  const isTopRank = candidate.rank === 1;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: `1px solid ${isTopRank ? 'var(--status-pass)' : 'var(--bg-tertiary)'}`,
      borderRadius: '8px',
      overflow: 'hidden',
      marginBottom: '16px',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--bg-tertiary)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: isTopRank ? 'rgba(52, 199, 89, 0.05)' : 'transparent'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ 
              fontSize: '14px', 
              fontWeight: 800, 
              color: isTopRank ? 'var(--text-primary)' : 'var(--text-muted)' 
            }}>
              Rank #{candidate.rank}
            </span>
            {isTopRank && isTiedTop && (
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: 'rgba(255, 159, 10, 0.15)',
                color: 'var(--status-gap)',
              }}>
                TIED TOP CANDIDATE (Abstention)
              </span>
            )}
            {isTopRank && !isTiedTop && (
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: 'rgba(52, 199, 89, 0.15)',
                color: 'var(--status-pass)',
              }}>
                TOP RANKED
              </span>
            )}
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{candidate.technique_id}</span>
            <span>—</span>
            <span>{candidate.technique_name}</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{
            fontSize: '28px',
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: isTopRank ? 'var(--status-pass)' : 'var(--text-primary)',
            lineHeight: 1,
          }}>
            {formatScore(candidate.final_ranking_score)}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase' }}>
            Final Ranking Score
          </div>
        </div>
      </div>

      {/* Details Body */}
      <div style={{ padding: '20px', display: 'flex', gap: '24px' }}>
        {/* Core details */}
        <div style={{ flex: '1.5' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
            {candidate.description}
          </div>
          
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
            Scoring Breakdown
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Temporal:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.temporal_score)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Host:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.host_score)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>User:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.user_score)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Process:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.process_score)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Technique:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.technique_score)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Graph:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{formatScore(candidate.graph_score)}</span>
            </div>
          </div>
        </div>

        {/* Feature Evidence */}
        <div style={{ flex: '1' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
            Supporting Evidence
          </div>
          {candidate.supporting_features.length > 0 ? (
            <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {candidate.supporting_features.map((feat, i) => (
                <li key={i}>{feat}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None found.</div>
          )}

          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', marginTop: '16px', letterSpacing: '0.5px' }}>
            Contradictory Evidence
          </div>
          {candidate.contradictory_features.length > 0 ? (
            <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '11px', color: 'var(--status-fail)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {candidate.contradictory_features.map((feat, i) => (
                <li key={i}>{feat}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>None found.</div>
          )}
        </div>
      </div>

      {/* Footer Scores */}
      <div style={{
        padding: '12px 20px',
        backgroundColor: 'var(--bg-primary)',
        borderTop: '1px solid var(--bg-tertiary)',
        display: 'flex',
        gap: '24px',
        fontSize: '11px',
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Deterministic:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{formatScore(candidate.deterministic_score)}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)' }}>ML Score:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{formatScore(candidate.ml_ranking_score)}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Model Version:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{candidate.model_version || 'N/A'}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Rank Method:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{candidate.rank_method}</span>
        </div>
      </div>
    </div>
  );
}

export function CandidatesView() {
  const { caseId } = useParams();
  const [data, setData] = useState<GapWithCandidates[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';
    setLoading(true);
    setError(null);

    getCandidates(scenarioId)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to retrieve candidates.');
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
          Generating and ranking reconstruction candidates...
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
              Candidate Generation Failed
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  // Filter to gaps that have candidates
  const itemsWithCandidates = data.filter(d => d.candidates && d.candidates.length > 0);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Information Panel */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--bg-tertiary)',
        borderRadius: '8px',
        padding: '20px',
        display: 'flex',
        gap: '24px'
      }}>
        <div style={{ flex: '1' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            How Candidates Are Ranked
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '12px' }}>
            CyberScope ranks potential missing events (candidates) to reconstruct the attack graph.
            Candidates are scored across 6 dimensions (Temporal, Host, User, Process, Technique, and Graph structure).
            This ranking <strong>suggests</strong> the most likely paths, but it does <strong>not</strong> prove them.
            Evidence Verification is the final arbiter.
          </div>
        </div>
        <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--bg-tertiary)' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Ranking Mode</span>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {data[0]?.analysis_metadata?.ranker_mode || 'DETERMINISTIC'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--bg-tertiary)' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>ML Model Version</span>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {data[0]?.analysis_metadata?.ml_model_version || 'N/A'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--bg-tertiary)' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Hybrid Alpha</span>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {data[0]?.analysis_metadata?.hybrid_alpha ?? 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {itemsWithCandidates.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No candidates generated. No critical gaps were found in this scenario.
        </div>
      ) : (
        itemsWithCandidates.map((item, index) => {
          const sortedCandidates = [...item.candidates].sort((a, b) => a.rank - b.rank);
          const topCandidates = sortedCandidates.filter(c => c.rank === 1);
          const isTiedTop = topCandidates.length > 1;

          return (
            <div key={item.gap.gap_id || index} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Gap: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{item.gap.gap_id}</span>
              </div>
              
              {isTiedTop && (
                <div style={{
                  padding: '12px 16px',
                  backgroundColor: 'rgba(255, 159, 10, 0.05)',
                  border: '1px solid rgba(255, 159, 10, 0.3)',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)'
                }}>
                  <strong style={{ color: 'var(--status-gap)' }}>Tie Detected:</strong> Multiple candidates share the rank #1 score. The engine abstains from selecting a single winner.
                </div>
              )}

              <div>
                {sortedCandidates.map(c => (
                  <CandidateCard key={c.candidate_id} candidate={c} isTiedTop={isTiedTop} />
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
