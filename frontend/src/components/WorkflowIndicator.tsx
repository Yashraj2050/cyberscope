

interface WorkflowIndicatorProps {
  currentStage: 'TELEMETRY' | 'GRAPH' | 'GAP' | 'CANDIDATES' | 'VERIFICATION' | 'DECISION';
  decision: "OBSERVED" | "INFERRED" | "UNKNOWN" | null;
}

export function WorkflowIndicator({ currentStage, decision }: WorkflowIndicatorProps) {
  const stages = [
    'TELEMETRY',
    'GRAPH',
    'GAP',
    'CANDIDATES',
    'VERIFY',
    'DECISION'
  ];

  // Map backend stages to UI stages
  const mappedCurrentStage = currentStage === 'VERIFICATION' ? 'VERIFY' : currentStage;
  const currentIndex = stages.indexOf(mappedCurrentStage);

  return (
    <div className="workflow-indicator" style={{ display: 'flex', gap: '8px', padding: '8px 24px' }}>
      {stages.map((stage, i) => {
        const isCompleted = i < currentIndex || (i === currentIndex && stage === 'DECISION');
        const isActive = i === currentIndex;
        
        return (
          <div key={stage} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className={`workflow-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
              {stage}
              {stage === 'DECISION' && decision && (
                <span className={`status-${decision}`} style={{ marginLeft: '4px' }}>
                  → {decision}
                </span>
              )}
            </div>
            {i < stages.length - 1 && <span style={{ color: 'var(--text-muted)' }}>↓</span>}
          </div>
        );
      })}
    </div>
  );
}
