import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { type CyberEvent, type FullPipelineResult, getEvents, runAnalysis } from '../services/api';

function EvidenceRow({ 
  event, 
  analysisResults 
}: { 
  event: CyberEvent, 
  analysisResults: FullPipelineResult[] 
}) {
  const [expanded, setExpanded] = useState(false);

  // Compute provenance / roles
  const roles: { type: 'GAP_BOUNDARY' | 'SUPPORTING' | 'CONTRADICTORY'; text: string }[] = [];
  
  analysisResults.forEach(res => {
    if (res.gap.previous_event_id === event.event_id) {
      roles.push({ type: 'GAP_BOUNDARY', text: `Precedes Gap ${res.gap.gap_id}` });
    }
    if (res.gap.next_event_id === event.event_id) {
      roles.push({ type: 'GAP_BOUNDARY', text: `Follows Gap ${res.gap.gap_id}` });
    }
    if (res.result?.supporting_evidence?.includes(event.event_id)) {
      roles.push({ type: 'SUPPORTING', text: `Supporting Evidence for ${res.result.technique_id || 'Candidate'}` });
    }
    if (res.result?.contradictory_evidence?.includes(event.event_id)) {
      roles.push({ type: 'CONTRADICTORY', text: `Contradicts ${res.result.technique_id || 'Candidate'}` });
    }
  });

  const uniqueRoles = Array.from(new Set(roles.map(r => JSON.stringify(r)))).map(r => JSON.parse(r) as typeof roles[0]);

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--bg-tertiary)',
      borderRadius: '8px',
      marginBottom: '8px',
      overflow: 'hidden'
    }}>
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '12px 16px',
          display: 'grid',
          gridTemplateColumns: '1.5fr 1fr 1fr 1fr 2fr',
          gap: '12px',
          alignItems: 'center',
          cursor: 'pointer',
          borderBottom: expanded ? '1px solid var(--bg-tertiary)' : 'none',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 600 }}>{event.event_id}</span>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{new Date(event.timestamp).toLocaleString()}</span>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{event.event_type}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{event.host_id}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{event.user_id || '-'}</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{event.process_name || event.technique_id || '-'}</span>
          <div style={{ display: 'flex', gap: '4px' }}>
            {uniqueRoles.slice(0, 2).map((role, i) => (
              <span key={i} style={{
                width: '8px', height: '8px', borderRadius: '50%',
                backgroundColor: role.type === 'GAP_BOUNDARY' ? 'var(--status-gap)' : 
                                 role.type === 'SUPPORTING' ? 'var(--status-pass)' : 'var(--status-fail)'
              }} title={role.text} />
            ))}
            {uniqueRoles.length > 2 && <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>+{uniqueRoles.length - 2}</span>}
          </div>
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '16px', display: 'flex', gap: '24px', backgroundColor: 'var(--bg-primary)' }}>
          
          {/* Provenance Panel */}
          <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                Provenance
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Source:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{event.source}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Status:</span>
                  <span style={{ color: 'var(--status-pass)', fontWeight: 600, fontSize: '10px', padding: '2px 6px', backgroundColor: 'rgba(52,199,89,0.1)', borderRadius: '4px' }}>
                    OBSERVED TELEMETRY
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Event ID:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.event_id}</span>
                </div>
                {event.source_event_id && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Source ID:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.source_event_id}</span>
                  </div>
                )}
              </div>
            </div>

            {uniqueRoles.length > 0 && (
              <div>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                  Role in Reconstruction
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {uniqueRoles.map((role, i) => (
                    <div key={i} style={{ 
                      fontSize: '11px', 
                      color: role.type === 'SUPPORTING' ? 'var(--status-pass)' : 
                             role.type === 'CONTRADICTORY' ? 'var(--status-fail)' : 'var(--status-gap)' 
                    }}>
                      • {role.text}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Raw Fields */}
          <div style={{ flex: '2', display: 'flex', flexDirection: 'column', gap: '16px', borderLeft: '1px solid var(--bg-tertiary)', paddingLeft: '24px' }}>
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                Relevant Details
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {event.process_id && <div style={{ fontSize: '12px' }}><span style={{ color: 'var(--text-muted)' }}>Process ID:</span> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.process_id}</span></div>}
                {event.parent_process_id && <div style={{ fontSize: '12px' }}><span style={{ color: 'var(--text-muted)' }}>Parent PID:</span> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.parent_process_id}</span></div>}
                {event.destination_ip && <div style={{ fontSize: '12px' }}><span style={{ color: 'var(--text-muted)' }}>Dest IP:</span> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.destination_ip}</span></div>}
                {event.destination_host && <div style={{ fontSize: '12px' }}><span style={{ color: 'var(--text-muted)' }}>Dest Host:</span> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{event.destination_host}</span></div>}
                {event.technique_name && <div style={{ fontSize: '12px', gridColumn: '1 / -1' }}><span style={{ color: 'var(--text-muted)' }}>Technique:</span> <span style={{ color: 'var(--text-primary)' }}>{event.technique_id} - {event.technique_name}</span></div>}
              </div>
            </div>

            {(event.metadata && Object.keys(event.metadata).length > 0) && (
              <div>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                  Metadata
                </div>
                <pre style={{ 
                  margin: 0, padding: '12px', backgroundColor: 'var(--bg-secondary)', 
                  borderRadius: '4px', fontSize: '11px', fontFamily: 'var(--font-mono)', 
                  color: 'var(--text-secondary)', overflowX: 'auto' 
                }}>
                  {JSON.stringify(event.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

export function EvidenceView() {
  const { caseId } = useParams();
  const [events, setEvents] = useState<CyberEvent[]>([]);
  const [analysis, setAnalysis] = useState<FullPipelineResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [search, setSearch] = useState('');

  useEffect(() => {
    const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';
    setLoading(true);
    setError(null);

    Promise.all([
      getEvents(scenarioId),
      runAnalysis(scenarioId).catch(() => []) // if analysis fails, we still show evidence
    ])
    .then(([evts, ans]) => {
      setEvents(evts);
      setAnalysis(ans);
      setLoading(false);
    })
    .catch(err => {
      setError(err.message || 'Failed to retrieve evidence data.');
      setLoading(false);
    });
  }, [caseId]);

  const filteredEvents = useMemo(() => {
    if (!search.trim()) return events;
    const lower = search.toLowerCase();
    return events.filter(e => 
      e.event_id.toLowerCase().includes(lower) ||
      e.host_id.toLowerCase().includes(lower) ||
      (e.user_id && e.user_id.toLowerCase().includes(lower)) ||
      e.event_type.toLowerCase().includes(lower) ||
      (e.process_name && e.process_name.toLowerCase().includes(lower))
    );
  }, [events, search]);

  if (loading) {
    return (
      <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
        <div style={{
          width: '32px', height: '32px', border: '3px solid var(--bg-tertiary)',
          borderTopColor: 'var(--accent-cyan)', borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Retrieving telemetry and evidence provenance...
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
              Failed to load evidence
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  const boundaryEvents = new Set<string>();
  analysis.forEach(a => {
    if (a.gap.previous_event_id) boundaryEvents.add(a.gap.previous_event_id);
    if (a.gap.next_event_id) boundaryEvents.add(a.gap.next_event_id);
  });

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Search and Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input 
            type="text" 
            placeholder="Search Event ID, Host, User, Process..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '300px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--bg-tertiary)',
              borderRadius: '6px',
              padding: '8px 12px',
              color: 'var(--text-primary)',
              fontSize: '13px',
              fontFamily: 'inherit'
            }}
          />
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Showing {filteredEvents.length} of {events.length} events
          </span>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--status-gap)' }}></span>
            <span style={{ color: 'var(--text-secondary)' }}>Gap Boundary</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--status-pass)' }}></span>
            <span style={{ color: 'var(--text-secondary)' }}>Supporting</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--status-fail)' }}></span>
            <span style={{ color: 'var(--text-secondary)' }}>Contradictory</span>
          </div>
        </div>
      </div>

      {/* Evidence List Header */}
      <div>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1.5fr 1fr 1fr 1fr 2fr', 
          gap: '12px', 
          padding: '0 16px 8px 16px',
          fontSize: '10px',
          fontWeight: 700,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          <div>Event ID / Time</div>
          <div>Type</div>
          <div>Host</div>
          <div>User</div>
          <div>Process / Technique</div>
        </div>

        {/* List */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {filteredEvents.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px dashed var(--bg-tertiary)' }}>
              No evidence matching the search criteria.
            </div>
          ) : (
            filteredEvents.map(evt => (
              <EvidenceRow key={evt.event_id} event={evt} analysisResults={analysis} />
            ))
          )}
        </div>
      </div>
      
    </div>
  );
}
