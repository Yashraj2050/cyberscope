import { useState } from 'react';
import type { FullPipelineResult, ReconstructionCandidate } from '../services/api';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface InvestigationInspectorProps {
  pipelineResult: FullPipelineResult | null;
}

export function InvestigationInspector({ pipelineResult }: InvestigationInspectorProps) {
  if (!pipelineResult) {
    return (
      <div className="inspector-panel" style={{ padding: '24px', color: 'var(--text-muted)' }}>
        <div className="section-header">INVESTIGATION INSPECTOR</div>
        <p>No active investigation. Run an analysis to view details.</p>
      </div>
    );
  }

  const { gap, candidates, result } = pipelineResult;
  const GAP_THRESHOLD = 0.40; // Default threshold

  return (
    <div className="inspector-panel">
      
      {/* SECTION 3 & 4: GAP AND SIGNALS */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--bg-tertiary)' }}>
        <div className="section-header">02 RECONSTRUCTION GAP</div>
        
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>Gap ID:</span>
            <span className="mono">{gap.gap_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>Previous Event:</span>
            <span className="mono">{gap.previous_event_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>Next Event:</span>
            <span className="mono">{gap.next_event_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>Gap Score:</span>
            <span className="mono">{gap.gap_score.toFixed(2)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-muted)' }}>
            <span>Threshold:</span>
            <span className="mono">{GAP_THRESHOLD.toFixed(2)}</span>
          </div>
          
          <div style={{ marginTop: '12px', padding: '12px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', border: '1px solid var(--bg-tertiary)' }}>
            <span className="badge badge-gap" style={{ marginBottom: '8px' }}>
              {gap.gap_score > GAP_THRESHOLD ? 'GAP DETECTED' : 'INSUFFICIENT GAP'}
            </span>
          </div>
        </div>

        <div className="section-header">GAP SIGNALS</div>
        <div className="signal-matrix">
          <SignalRow label="Technique Transition" value={gap.detection_signals.technique_transition} />
          <SignalRow label="Behavioral Prerequisite" value={gap.detection_signals.behavioral_prerequisite} />
          <SignalRow label="Host Continuity" value={gap.detection_signals.host_continuity} />
          <SignalRow label="User Continuity" value={gap.detection_signals.user_continuity} />
          <SignalRow label="Process Relationship" value={gap.detection_signals.process_relationship} />
          <SignalRow label="Temporal Gap" value={gap.detection_signals.temporal} />
        </div>
      </div>

      {/* SECTION 5: CANDIDATES */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--bg-tertiary)' }}>
        <div className="section-header">03 CANDIDATE GENERATION</div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Candidates Generated: {candidates.length}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {candidates.map((c, i) => {
            const isTie = i > 0 && candidates[i - 1].candidate_score === c.candidate_score;
            return <CandidateCard key={c.candidate_id} candidate={c} isTie={isTie} />;
          })}
        </div>
      </div>

      {/* SECTION 6 & 7: VERIFICATION AND DECISION */}
      <div style={{ padding: '24px' }}>
        <div className="section-header">04 EVIDENCE VERIFICATION</div>
        
        <div className="signal-matrix" style={{ marginBottom: '24px' }}>
          {Object.entries(result.verification_checks).map(([check, status]) => {
            const icon = status === 'PASS' ? '✓ ' : status === 'FAIL' ? '✕ ' : '? ';
            return (
              <div className="matrix-row" key={check}>
                <span style={{ textTransform: 'capitalize' }}>{check.replace(/_/g, ' ')}</span>
                <span className={`badge badge-${status.toLowerCase()}`}>{icon}{status}</span>
              </div>
            );
          })}
        </div>

        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700 }}>VERIFICATION SCORE</span>
            <span className="mono" style={{ fontWeight: 700 }}>{result.verification_score.toFixed(2)}</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            Evidence strength: {result.confidence_label}
            <br />
            <span style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>Verification score is an evidence-strength score, not a probability.</span>
          </div>
        </div>

        <ExpandableSection title="SUPPORTING EVIDENCE" items={result.supporting_evidence} />
        <ExpandableSection title="MISSING EVIDENCE" items={result.missing_evidence} />
        <ExpandableSection title="CONTRADICTORY EVIDENCE" items={result.contradictory_evidence} />
        
        <div className="decision-card">
          <div className="decision-title">RECONSTRUCTION STATUS</div>
          <div className={`decision-status status-${result.status}`}>{result.status}</div>
          {result.status === 'UNKNOWN' && (
            <div style={{ fontSize: '13px', marginBottom: '8px' }}>
              Evidence insufficient to establish a definitive reconstruction.
            </div>
          )}
          {result.status === 'INFERRED' && (
            <div style={{ fontSize: '13px', marginBottom: '8px' }}>
              Candidate supported by sufficient contextual evidence.
            </div>
          )}
          {result.status === 'OBSERVED' && (
            <div style={{ fontSize: '13px', marginBottom: '8px' }}>
              Direct telemetry evidence exists.
            </div>
          )}
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Evidence Strength: {result.confidence_label}
          </div>
          <div style={{ fontSize: '13px', lineHeight: '1.4' }}>
            <strong>REASON:</strong> {result.explanation}
          </div>
        </div>

      </div>
    </div>
  );
}

// ---------------- Helper Components ----------------

function SignalRow({ label, value }: { label: string, value: boolean }) {
  return (
    <div className="matrix-row">
      <span>{label}</span>
      <span className={`badge badge-${value ? 'pass' : 'fail'}`}>
        {value ? 'PASS' : 'FAIL'}
      </span>
    </div>
  );
}

function CandidateCard({ candidate, isTie }: { candidate: ReconstructionCandidate, isTie: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
      <div 
        style={{ padding: '12px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>
            RANK {candidate.rank} {isTie ? '(TIE)' : ''}
          </div>
          <div className="mono" style={{ fontWeight: 600 }}>{candidate.technique_id}</div>
          <div style={{ fontSize: '12px', marginTop: '4px' }}>{candidate.technique_name}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="mono" style={{ fontSize: '14px', fontWeight: 700 }}>{candidate.candidate_score.toFixed(4)}</div>
          {expanded ? <ChevronDown size={14} style={{ marginTop: '8px', color: 'var(--text-muted)' }} /> : <ChevronRight size={14} style={{ marginTop: '8px', color: 'var(--text-muted)' }} />}
        </div>
      </div>
      
      {expanded && (
        <div style={{ padding: '12px', borderTop: '1px solid var(--bg-tertiary)', fontSize: '11px' }}>
          <div style={{ fontWeight: 700, marginBottom: '12px', letterSpacing: '1px', color: 'var(--text-muted)' }}>
            EVIDENCE SUPPORT SCORE
          </div>
          <div className="signal-matrix" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <ProgressBar label="TECHNIQUE COMPATIBILITY" value={candidate.technique_score} />
            <ProgressBar label="BEHAVIORAL COMPATIBILITY" value={candidate.graph_score} />
            <ProgressBar label="HOST COMPATIBILITY" value={candidate.host_score} />
            <ProgressBar label="USER COMPATIBILITY" value={candidate.user_score} />
            <ProgressBar label="PROCESS COMPATIBILITY" value={candidate.process_score} />
            <ProgressBar label="TEMPORAL COMPATIBILITY" value={candidate.temporal_score} />
          </div>
          <div style={{ marginTop: '12px', fontStyle: 'italic', color: 'var(--text-muted)' }}>
            Candidate score ≠ probability. It is an evidence-based ranking score.
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressBar({ label, value }: { label: string, value: number }) {
  const filled = Math.round(value * 16);
  const empty = 16 - filled;
  const bar = '█'.repeat(Math.max(0, filled)) + '░'.repeat(Math.max(0, empty));
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)' }}>
      <span>{label}</span>
      <span>{bar} {value.toFixed(2)}</span>
    </div>
  );
}

function ExpandableSection({ title, items }: { title: string, items: string[] }) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div style={{ marginBottom: '12px' }}>
      <div 
        style={{ display: 'flex', alignItems: 'center', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', cursor: 'pointer', marginBottom: expanded ? '8px' : '0' }}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={14} style={{ marginRight: '4px' }} /> : <ChevronRight size={14} style={{ marginRight: '4px' }} />}
        {title}
      </div>
      
      {expanded && (
        <ul style={{ listStyleType: 'disc', paddingLeft: '24px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          {items.length === 0 ? (
            <li style={{ listStyleType: 'none', marginLeft: '-24px', fontStyle: 'italic' }}>NONE IDENTIFIED</li>
          ) : (
            items.map((item, i) => <li key={i} style={{ marginBottom: '4px' }}>{item}</li>)
          )}
        </ul>
      )}
    </div>
  );
}
