import { type ReconstructionGap } from '../services/api';

interface TimelineProps {
  gap: ReconstructionGap;
  selectedNode: string | null;
  onSelectNode: (nodeId: string) => void;
}

export function Timeline({ gap, selectedNode, onSelectNode }: TimelineProps) {
  
  // Format timestamp (just extract the time portion for brevity if possible, or use as is)
  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return ts;
      return d.toISOString().substring(11, 23); // HH:mm:ss.SSS
    } catch {
      return ts;
    }
  };

  return (
    <div className="timeline-container">
      <div className="timeline-track">
        
        {/* Previous Event */}
        <div 
          className={`timeline-event ${selectedNode === 'prev' ? 'selected' : ''}`}
          onClick={() => onSelectNode('prev')}
        >
          <div className="timeline-time mono">{formatTime(gap.start_timestamp)}</div>
          <div className="timeline-dot"></div>
          <div className="timeline-id mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{gap.previous_event_id}</div>
        </div>

        <div className="timeline-connector gap"></div>
        
        {/* Gap Location */}
        <div 
          className={`timeline-event gap ${selectedNode === 'gap' ? 'selected' : ''}`}
          onClick={() => onSelectNode('gap')}
        >
          <div className="timeline-time mono" style={{ visibility: 'hidden' }}>00:00:00</div>
          <div className="timeline-dot"></div>
          <div className="timeline-id mono" style={{ fontSize: '10px', color: 'var(--status-inferred)' }}>{gap.gap_id}</div>
        </div>

        <div className="timeline-connector gap"></div>
        
        {/* Next Event */}
        <div 
          className={`timeline-event ${selectedNode === 'next' ? 'selected' : ''}`}
          onClick={() => onSelectNode('next')}
        >
          <div className="timeline-time mono">{formatTime(gap.end_timestamp)}</div>
          <div className="timeline-dot"></div>
          <div className="timeline-id mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{gap.next_event_id}</div>
        </div>
        
      </div>
    </div>
  );
}
