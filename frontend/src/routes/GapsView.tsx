import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { type ReconstructionGap, getGaps } from '../services/api';

const GAP_SCORE_THRESHOLD = 0.40;

const SIGNAL_META: Record<string, { label: string; weight: number; icon: string; description: string }> = {
  technique_transition:    { label: 'Technique Transition',    weight: 0.30, icon: '⬆', description: 'Stage jump between adjacent events exceeds expected progression' },
  behavioral_prerequisite: { label: 'Behavioral Prerequisite', weight: 0.25, icon: '⚡', description: 'Missing prerequisite activity expected before the observed behavior' },
  host_continuity:         { label: 'Host Continuity',         weight: 0.15, icon: '🖥', description: 'Host context changes unexpectedly between adjacent events' },
  user_continuity:         { label: 'User Continuity',         weight: 0.10, icon: '👤', description: 'User identity changes without an authentication event' },
  process_relationship:    { label: 'Process Relationship',    weight: 0.10, icon: '⚙', description: 'No parent-child process lineage between adjacent events' },
  temporal:                { label: 'Temporal',                weight: 0.10, icon: '⏱', description: 'Abnormally large time gap between consecutive events' },
};

const SIGNAL_ORDER = ['technique_transition', 'behavioral_prerequisite', 'host_continuity', 'user_continuity', 'process_relationship', 'temporal'];

function formatSeconds(s: number): string {
  if (s < 60) return `${s.toFixed(1)}s`;
  if (s < 3600) return `${(s / 60).toFixed(1)}m`;
  return `${(s / 3600).toFixed(1)}h`;
}

function SignalBar({ signalKey, fired }: { signalKey: string; fired: boolean }) {
  const meta = SIGNAL_META[signalKey];
  if (!meta) return null;
  const contribution = fired ? meta.weight : 0;
  const pct = Math.round(contribution * 100);
  const barMaxPct = Math.round(meta.weight * 100);

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
          <span>{meta.icon}</span>
          <span style={{ fontWeight: 600 }}>{meta.label}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
          <span style={{
            padding: '1px 6px',
            borderRadius: '3px',
            fontWeight: 700,
            fontSize: '10px',
            backgroundColor: fired ? 'rgba(255, 159, 10, 0.15)' : 'rgba(155, 161, 166, 0.1)',
            color: fired ? 'var(--status-gap)' : 'var(--text-muted)',
          }}>
            {fired ? 'FIRED' : 'CLEAR'}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', color: fired ? 'var(--status-gap)' : 'var(--text-muted)' }}>
            +{pct}%
          </span>
        </div>
      </div>
      {/* Bar */}
      <div style={{
        width: '100%',
        height: '6px',
        backgroundColor: 'var(--bg-primary)',
        borderRadius: '3px',
        overflow: 'hidden',
        position: 'relative',
      }}>
        {/* Max possible */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: '100%',
          width: `${barMaxPct * 3.33}%`,
          backgroundColor: 'var(--bg-tertiary)',
          borderRadius: '3px',
        }} />
        {/* Actual contribution */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: '100%',
          width: `${pct * 3.33}%`,
          backgroundColor: fired ? 'var(--status-gap)' : 'transparent',
          borderRadius: '3px',
          transition: 'width 0.5s ease',
        }} />
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px' }}>
        {meta.description}
      </div>
    </div>
  );
}

function GapCard({ gap }: { gap: ReconstructionGap }) {
  const isDetected = gap.gap_score >= GAP_SCORE_THRESHOLD;
  const scorePct = Math.round(gap.gap_score * 100);
  const thresholdPct = Math.round(GAP_SCORE_THRESHOLD * 100);

  const signals = gap.detection_signals;
  const firedCount = SIGNAL_ORDER.filter(k => (signals as any)[k] === true).length;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: `1px solid ${isDetected ? 'var(--status-gap)' : 'var(--bg-tertiary)'}`,
      borderRadius: '8px',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--bg-tertiary)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 700 }}>
              {gap.gap_id}
            </span>
            <span style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 700,
              backgroundColor: isDetected ? 'rgba(255, 159, 10, 0.15)' : 'rgba(52, 199, 89, 0.1)',
              color: isDetected ? 'var(--status-gap)' : 'var(--status-pass)',
            }}>
              {isDetected ? 'GAP DETECTED' : 'NO GAP DETECTED'}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {firedCount} of 6 signals fired · {formatSeconds(gap.temporal_gap_seconds)} temporal window
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{
            fontSize: '28px',
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: isDetected ? 'var(--status-gap)' : 'var(--status-pass)',
            lineHeight: 1,
          }}>
            {scorePct}%
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            THRESHOLD {thresholdPct}%
          </div>
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: '20px', display: 'flex', gap: '24px' }}>

        {/* Left: Event Pair */}
        <div style={{ flex: '0 0 240px' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px', letterSpacing: '0.5px' }}>
            Event Transition
          </div>

          {/* Preceding */}
          <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--bg-tertiary)', borderRadius: '6px', padding: '12px', marginBottom: '8px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>PRECEDING EVENT</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', marginBottom: '2px', wordBreak: 'break-all' }}>{gap.previous_event_id}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{gap.previous_event_type}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>{new Date(gap.start_timestamp).toLocaleString()}</div>
          </div>

          {/* Arrow */}
          <div style={{ textAlign: 'center', color: isDetected ? 'var(--status-gap)' : 'var(--text-muted)', fontSize: '16px', margin: '4px 0' }}>
            ↓ {isDetected && <span style={{ fontSize: '11px' }}>GAP</span>} ↓
          </div>

          {/* Following */}
          <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--bg-tertiary)', borderRadius: '6px', padding: '12px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>FOLLOWING EVENT</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', marginBottom: '2px', wordBreak: 'break-all' }}>{gap.next_event_id}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{gap.next_event_type}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>{new Date(gap.end_timestamp).toLocaleString()}</div>
          </div>

          {/* Context */}
          <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
            {gap.affected_host && <div>Host: <span style={{ color: 'var(--text-secondary)' }}>{gap.affected_host}</span></div>}
            {gap.affected_user && <div>User: <span style={{ color: 'var(--text-secondary)' }}>{gap.affected_user}</span></div>}
            <div>Status: <span style={{ color: 'var(--text-secondary)' }}>{gap.status}</span></div>
          </div>
        </div>

        {/* Right: Signal Analysis */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.5px' }}>
            Detection Signals
          </div>

          {SIGNAL_ORDER.map(key => (
            <SignalBar key={key} signalKey={key} fired={(signals as any)[key] === true} />
          ))}

          {/* Gap Score Gauge */}
          <div style={{ marginTop: '16px', backgroundColor: 'var(--bg-primary)', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Composite Gap Score
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 700,
                color: isDetected ? 'var(--status-gap)' : 'var(--status-pass)',
              }}>
                {gap.gap_score.toFixed(4)}
              </span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute', left: 0, top: 0, height: '100%',
                width: `${scorePct}%`,
                backgroundColor: isDetected ? 'var(--status-gap)' : 'var(--status-pass)',
                borderRadius: '4px',
                transition: 'width 0.5s ease',
              }} />
              {/* Threshold marker */}
              <div style={{
                position: 'absolute', left: `${thresholdPct}%`, top: '-2px',
                width: '2px', height: '12px',
                backgroundColor: 'var(--text-primary)',
                opacity: 0.6,
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              <span>0.00</span>
              <span>Threshold: {GAP_SCORE_THRESHOLD.toFixed(2)}</span>
              <span>1.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* Why Detected / Not Detected */}
      {isDetected && (
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--bg-tertiary)',
          backgroundColor: 'rgba(255, 159, 10, 0.03)',
        }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--status-gap)', textTransform: 'uppercase', marginBottom: '6px', letterSpacing: '0.5px' }}>
            Why This Gap Was Detected
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {buildExplanation(gap)}
          </div>
        </div>
      )}
    </div>
  );
}

function buildExplanation(gap: ReconstructionGap): string {
  const parts: string[] = [];
  const s = gap.detection_signals;

  if (s.technique_transition) {
    parts.push(`The ATT&CK technique stage jumps from ${gap.previous_event_type} to ${gap.next_event_type}, indicating a missing intermediate step.`);
  }
  if (s.behavioral_prerequisite) {
    parts.push(`A behavioral prerequisite expected before the following event was not found in the observed telemetry.`);
  }
  if (s.host_continuity) {
    parts.push(`The host context changes${gap.affected_host ? ` (${gap.affected_host})` : ''} without a network or lateral movement event.`);
  }
  if (s.user_continuity) {
    parts.push(`The user identity changes${gap.affected_user ? ` (${gap.affected_user})` : ''} without an authentication event.`);
  }
  if (s.process_relationship) {
    parts.push(`No parent-child process relationship exists between the adjacent events.`);
  }
  if (s.temporal) {
    parts.push(`The temporal gap of ${formatSeconds(gap.temporal_gap_seconds)} exceeds the expected inter-event interval.`);
  }

  if (parts.length === 0) {
    return `Gap score ${gap.gap_score.toFixed(4)} exceeds the detection threshold of ${GAP_SCORE_THRESHOLD.toFixed(2)}.`;
  }

  return parts.join(' ');
}

export function GapsView() {
  const { caseId } = useParams();
  const [gaps, setGaps] = useState<ReconstructionGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';
    setLoading(true);
    setError(null);

    getGaps(scenarioId)
      .then(data => {
        setGaps(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to retrieve gap analysis.');
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
          Running gap detection on observed telemetry...
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
              Gap Detection Failed
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  const detectedGaps = gaps.filter(g => g.gap_score >= GAP_SCORE_THRESHOLD);
  const belowThreshold = gaps.filter(g => g.gap_score < GAP_SCORE_THRESHOLD);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Summary Bar */}
      <div style={{
        display: 'flex',
        gap: '16px',
        padding: '16px 20px',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--bg-tertiary)',
        borderRadius: '8px',
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
            Transitions Analyzed
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{gaps.length}</div>
        </div>
        <div style={{ width: '1px', backgroundColor: 'var(--bg-tertiary)' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
            Gaps Detected
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: detectedGaps.length > 0 ? 'var(--status-gap)' : 'var(--status-pass)' }}>
            {detectedGaps.length}
          </div>
        </div>
        <div style={{ width: '1px', backgroundColor: 'var(--bg-tertiary)' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
            Below Threshold
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--status-pass)' }}>
            {belowThreshold.length}
          </div>
        </div>
        <div style={{ width: '1px', backgroundColor: 'var(--bg-tertiary)' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
            Detection Threshold
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{(GAP_SCORE_THRESHOLD * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Gap Cards */}
      {detectedGaps.length > 0 && (
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--status-gap)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>
            Detected Gaps ({detectedGaps.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {detectedGaps.map((gap) => (
              <GapCard key={gap.gap_id} gap={gap} />
            ))}
          </div>
        </div>
      )}

      {belowThreshold.length > 0 && (
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>
            Below Threshold ({belowThreshold.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {belowThreshold.map((gap) => (
              <GapCard key={gap.gap_id} gap={gap} />
            ))}
          </div>
        </div>
      )}

      {gaps.length === 0 && (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No event transitions were analyzed for gaps in this scenario.
        </div>
      )}
    </div>
  );
}
