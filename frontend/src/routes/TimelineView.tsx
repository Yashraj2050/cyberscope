import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { type CyberEvent, type ReconstructionGap, getEvents, getGaps } from '../services/api';
import { ChevronDown, ChevronRight, Activity, Zap, Search } from 'lucide-react';

type TimelineItem = 
  | { type: 'EVENT'; data: CyberEvent; timestampMs: number }
  | { type: 'GAP'; data: ReconstructionGap; timestampMs: number };

export function TimelineView() {
  const { caseId } = useParams();
  const [events, setEvents] = useState<CyberEvent[]>([]);
  const [gaps, setGaps] = useState<ReconstructionGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [search, setSearch] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getEvents(scenarioId),
      getGaps(scenarioId)
    ])
    .then(([evts, gps]) => {
      setEvents(evts);
      setGaps(gps);
    })
    .catch(err => setError(err.message || 'Failed to fetch timeline data'))
    .finally(() => setLoading(false));
  }, [scenarioId]);

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading timeline...</div>;
  }
  if (error) {
    return <div style={{ padding: '40px', color: 'var(--status-fail)' }}>Error: {error}</div>;
  }

  // 1. Build chronological timeline
  const timeline: TimelineItem[] = [];
  
  events.forEach(e => {
    timeline.push({ type: 'EVENT', data: e, timestampMs: new Date(e.timestamp).getTime() });
  });

  gaps.forEach(g => {
    // Position the gap visually halfway between its surrounding events
    const start = new Date(g.start_timestamp).getTime();
    const end = new Date(g.end_timestamp).getTime();
    const mid = start + (end - start) / 2;
    timeline.push({ type: 'GAP', data: g, timestampMs: mid });
  });

  // Sort strictly by timestamp
  timeline.sort((a, b) => a.timestampMs - b.timestampMs);

  // Search filter
  const filteredTimeline = timeline.filter(item => {
    if (!search) return true;
    const q = search.toLowerCase();
    if (item.type === 'EVENT') {
      const e = item.data;
      return (
        e.event_id.toLowerCase().includes(q) ||
        e.event_type.toLowerCase().includes(q) ||
        (e.host_id || '').toLowerCase().includes(q) ||
        (e.user_id || '').toLowerCase().includes(q) ||
        (e.process_name || '').toLowerCase().includes(q) ||
        (e.technique_id || '').toLowerCase().includes(q)
      );
    } else {
      const g = item.data;
      return g.gap_id.toLowerCase().includes(q);
    }
  });

  // Summary stats
  const totalEvents = events.length;
  const earliest = events.length > 0 ? new Date(Math.min(...events.map(e => new Date(e.timestamp).getTime()))).toISOString() : 'N/A';
  const latest = events.length > 0 ? new Date(Math.max(...events.map(e => new Date(e.timestamp).getTime()))).toISOString() : 'N/A';
  const spanMs = (events.length > 0) ? (new Date(latest).getTime() - new Date(earliest).getTime()) : 0;
  const spanHours = (spanMs / (1000 * 60 * 60)).toFixed(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 48px)', boxSizing: 'border-box' }}>
      
      {/* Header & Controls */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--bg-tertiary)', backgroundColor: 'var(--bg-primary)' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 16px 0' }}>Investigation Timeline</h2>
        
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          {/* Summary */}
          <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>Observed Events</div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{totalEvents}</div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>Detected Gaps</div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--status-gap)' }}>{gaps.length}</div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>Time Span</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{spanHours} hrs</div>
            </div>
          </div>

          {/* Search */}
          <div style={{ flex: '1', display: 'flex', alignItems: 'flex-end' }}>
            <div style={{ position: 'relative', width: '100%', maxWidth: '400px' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search events, hosts, techniques..."
                style={{
                  width: '100%',
                  padding: '10px 10px 10px 36px',
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--bg-tertiary)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Timeline Scrollable Area */}
      <div style={{ flex: '1', overflowY: 'auto', padding: '24px' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', position: 'relative' }}>
          
          {/* Vertical spine */}
          <div style={{ position: 'absolute', left: '120px', top: '0', bottom: '0', width: '2px', backgroundColor: 'var(--bg-tertiary)', zIndex: 0 }}></div>

          {filteredTimeline.map((item) => {
            if (item.type === 'EVENT') {
              const e = item.data;
              const isExpanded = expandedItems.has(e.event_id);
              
              return (
                <div key={e.event_id} style={{ display: 'flex', gap: '24px', marginBottom: '16px', position: 'relative', zIndex: 1 }}>
                  {/* Timestamp */}
                  <div style={{ width: '96px', textAlign: 'right', paddingTop: '12px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {e.timestamp.replace('T', ' ').replace('Z', '')}
                  </div>
                  
                  {/* Node */}
                  <div style={{ width: '24px', display: 'flex', justifyContent: 'center', paddingTop: '10px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--accent-cyan)', border: '2px solid var(--bg-primary)' }}></div>
                  </div>
                  
                  {/* Card */}
                  <div style={{ flex: '1' }}>
                    <div 
                      onClick={() => toggleExpand(e.event_id)}
                      style={{ 
                        backgroundColor: 'var(--bg-secondary)', 
                        border: '1px solid var(--bg-tertiary)', 
                        borderRadius: '6px', 
                        padding: '12px', 
                        cursor: 'pointer',
                        transition: 'border-color 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span style={{ fontSize: '10px', padding: '2px 6px', backgroundColor: 'rgba(100,210,255,0.1)', color: 'var(--accent-cyan)', borderRadius: '4px', fontWeight: 700 }}>OBSERVED</span>
                            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{e.event_id}</span>
                          </div>
                          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                            {e.event_type}
                          </div>
                          <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                            {e.host_id && <span><span style={{color: 'var(--text-muted)'}}>Host:</span> {e.host_id}</span>}
                            {e.user_id && <span><span style={{color: 'var(--text-muted)'}}>User:</span> {e.user_id}</span>}
                            {e.technique_id && <span><span style={{color: 'var(--text-muted)'}}>Technique:</span> {e.technique_id}</span>}
                          </div>
                        </div>
                        {isExpanded ? <ChevronDown size={16} color="var(--text-muted)"/> : <ChevronRight size={16} color="var(--text-muted)"/>}
                      </div>
                      
                      {isExpanded && (
                        <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--bg-tertiary)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', marginBottom: '12px' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Process:</span>
                            <span style={{ fontFamily: 'var(--font-mono)' }}>{e.process_name || '-'} (PID: {e.process_id || '-'})</span>
                            
                            <span style={{ color: 'var(--text-muted)' }}>Source:</span>
                            <span>{e.source || '-'}</span>
                            
                            {e.destination_ip && (
                              <>
                                <span style={{ color: 'var(--text-muted)' }}>Dest IP:</span>
                                <span>{e.destination_ip}</span>
                              </>
                            )}
                          </div>
                          
                          {e.metadata && Object.keys(e.metadata).length > 0 && (
                            <div>
                              <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Metadata:</span>
                              <pre style={{ margin: 0, padding: '8px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                                {JSON.stringify(e.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            } else {
              const g = item.data;
              return (
                <div key={g.gap_id} style={{ display: 'flex', gap: '24px', margin: '32px 0', position: 'relative', zIndex: 1 }}>
                  <div style={{ width: '96px', textAlign: 'right', paddingTop: '12px', fontSize: '11px', color: 'var(--status-gap)', fontWeight: 600 }}>
                    ~ {g.temporal_gap_seconds.toFixed(0)}s
                  </div>
                  
                  <div style={{ width: '24px', display: 'flex', justifyContent: 'center', paddingTop: '8px' }}>
                    <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: 'var(--bg-primary)', border: '2px dashed var(--status-gap)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Activity size={10} color="var(--status-gap)" />
                    </div>
                  </div>
                  
                  <div style={{ flex: '1' }}>
                    <div style={{ 
                        backgroundColor: 'rgba(255, 159, 10, 0.05)', 
                        border: '1px dashed var(--status-gap)', 
                        borderRadius: '6px', 
                        padding: '16px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Zap size={14} color="var(--status-gap)" />
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--status-gap)' }}>DETECTED GAP</span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Score: <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{g.gap_score.toFixed(2)}</span></div>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Evidence incomplete. Discontinuity detected between <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{g.previous_event_id}</span> and <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{g.next_event_id}</span>.
                      </div>
                    </div>
                  </div>
                </div>
              );
            }
          })}

        </div>
      </div>
    </div>
  );
}
