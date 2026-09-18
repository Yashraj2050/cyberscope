import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { type CyberEvent, getEvents } from '../services/api';
import { Search, ChevronDown, ChevronRight, Server, User, TerminalSquare, Zap, Clock, ShieldAlert } from 'lucide-react';

export function TelemetryView() {
  const { caseId } = useParams();
  const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';

  const [events, setEvents] = useState<CyberEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  
  // Sort direction: 'desc' = newest first, 'asc' = oldest first
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('asc');

  // Filters
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [selectedHosts, setSelectedHosts] = useState<Set<string>>(new Set());
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [selectedTechniques, setSelectedTechniques] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    getEvents(scenarioId)
      .then(data => {
        // Double-check to never expose ground truth if the backend accidentally leaks it.
        const safeEvents = data.filter(e => e.event_id !== 'EVT-003' && !e.event_id.toLowerCase().includes('hidden'));
        setEvents(safeEvents);
      })
      .catch(err => setError(err.message || 'Failed to fetch telemetry'))
      .finally(() => setLoading(false));
  }, [scenarioId]);

  // Derived filter options
  const filterOptions = useMemo(() => {
    const types = new Set<string>();
    const hosts = new Set<string>();
    const users = new Set<string>();
    const techniques = new Set<string>();

    events.forEach(e => {
      if (e.event_type) types.add(e.event_type);
      if (e.host_id) hosts.add(e.host_id);
      if (e.user_id) users.add(e.user_id);
      if (e.technique_id) techniques.add(e.technique_id);
    });

    return {
      types: Array.from(types).sort(),
      hosts: Array.from(hosts).sort(),
      users: Array.from(users).sort(),
      techniques: Array.from(techniques).sort()
    };
  }, [events]);

  // Summary Metrics
  const summary = useMemo(() => {
    if (events.length === 0) return null;
    const processes = new Set(events.map(e => e.process_name).filter(Boolean));
    const sortedTimes = events.map(e => new Date(e.timestamp).getTime()).sort();
    const spanMs = sortedTimes[sortedTimes.length - 1] - sortedTimes[0];
    const spanHrs = (spanMs / (1000 * 60 * 60)).toFixed(1);

    return {
      count: events.length,
      hostCount: filterOptions.hosts.length,
      userCount: filterOptions.users.length,
      processCount: processes.size,
      techniqueCount: filterOptions.techniques.length,
      spanHrs
    };
  }, [events, filterOptions]);

  // Filter & Sort
  const processedEvents = useMemo(() => {
    let filtered = events;

    // Apply Search
    if (search.trim()) {
      const q = search.toLowerCase();
      filtered = filtered.filter(e => 
        (e.event_id && e.event_id.toLowerCase().includes(q)) ||
        (e.event_type && e.event_type.toLowerCase().includes(q)) ||
        (e.host_id && e.host_id.toLowerCase().includes(q)) ||
        (e.user_id && e.user_id.toLowerCase().includes(q)) ||
        (e.process_name && e.process_name.toLowerCase().includes(q)) ||
        (e.technique_id && e.technique_id.toLowerCase().includes(q)) ||
        (e.source_event_id && e.source_event_id.toLowerCase().includes(q)) ||
        (e.destination_host && e.destination_host.toLowerCase().includes(q)) ||
        (e.destination_ip && e.destination_ip.toLowerCase().includes(q))
      );
    }

    // Apply Dropdown Filters
    if (selectedTypes.size > 0) filtered = filtered.filter(e => selectedTypes.has(e.event_type));
    if (selectedHosts.size > 0) filtered = filtered.filter(e => selectedHosts.has(e.host_id));
    if (selectedUsers.size > 0) filtered = filtered.filter(e => e.user_id && selectedUsers.has(e.user_id));
    if (selectedTechniques.size > 0) filtered = filtered.filter(e => e.technique_id && selectedTechniques.has(e.technique_id));

    // Sort
    filtered.sort((a, b) => {
      const tA = new Date(a.timestamp).getTime();
      const tB = new Date(b.timestamp).getTime();
      return sortDir === 'asc' ? tA - tB : tB - tA;
    });

    return filtered;
  }, [events, search, selectedTypes, selectedHosts, selectedUsers, selectedTechniques, sortDir]);

  const toggleRow = (id: string) => {
    const next = new Set(expandedRows);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedRows(next);
  };

  const toggleFilter = (setFn: React.Dispatch<React.SetStateAction<Set<string>>>, value: string) => {
    setFn(prev => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  };

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading telemetry...</div>;
  if (error) return <div style={{ padding: '40px', color: 'var(--status-fail)' }}>Error: {error}</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      
      {/* Header & Summary */}
      <div style={{ padding: '24px', backgroundColor: 'var(--bg-primary)', borderBottom: '1px solid var(--bg-tertiary)' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 16px 0' }}>Telemetry</h2>
        
        <div style={{ padding: '12px 16px', backgroundColor: 'rgba(255,204,0,0.1)', border: '1px solid rgba(255,204,0,0.3)', borderRadius: '6px', display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px' }}>
          <ShieldAlert size={20} color="#FFCC00" />
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#FFCC00', letterSpacing: '0.5px' }}>OBSERVED TELEMETRY</div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              These records are directly observed input to the reconstruction engine. Missing events are not inserted into this table.
            </div>
          </div>
        </div>

        {summary && (
          <div style={{ display: 'flex', gap: '32px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Observed Events</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.count}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Hosts</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.hostCount}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Users</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.userCount}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Processes</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.processCount}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Techniques</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.techniqueCount}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Time Span</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{summary.spanHrs} hrs</span>
            </div>
          </div>
        )}

        {/* Controls */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by ID, Host, IP, Technique..."
              style={{
                width: '100%',
                padding: '8px 8px 8px 32px',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--bg-tertiary)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            {filterOptions.types.map(t => (
              <button 
                key={t}
                onClick={() => toggleFilter(setSelectedTypes, t)}
                style={{
                  padding: '4px 10px',
                  fontSize: '11px',
                  borderRadius: '12px',
                  border: `1px solid ${selectedTypes.has(t) ? 'var(--accent-cyan)' : 'var(--bg-tertiary)'}`,
                  backgroundColor: selectedTypes.has(t) ? 'rgba(50,215,255,0.1)' : 'var(--bg-secondary)',
                  color: selectedTypes.has(t) ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >{t}</button>
            ))}
            {filterOptions.hosts.map(h => (
              <button 
                key={h}
                onClick={() => toggleFilter(setSelectedHosts, h)}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '12px', border: `1px solid ${selectedHosts.has(h) ? '#AF52DE' : 'var(--bg-tertiary)'}`, backgroundColor: selectedHosts.has(h) ? 'rgba(175,82,222,0.1)' : 'var(--bg-secondary)', color: selectedHosts.has(h) ? '#AF52DE' : 'var(--text-secondary)', cursor: 'pointer' }}
              >{h}</button>
            ))}
            {filterOptions.users.map(u => (
              <button 
                key={u}
                onClick={() => toggleFilter(setSelectedUsers, u)}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '12px', border: `1px solid ${selectedUsers.has(u) ? '#FF9500' : 'var(--bg-tertiary)'}`, backgroundColor: selectedUsers.has(u) ? 'rgba(255,149,0,0.1)' : 'var(--bg-secondary)', color: selectedUsers.has(u) ? '#FF9500' : 'var(--text-secondary)', cursor: 'pointer' }}
              >{u}</button>
            ))}
            {filterOptions.techniques.map(t => (
              <button 
                key={t}
                onClick={() => toggleFilter(setSelectedTechniques, t)}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '12px', border: `1px solid ${selectedTechniques.has(t) ? '#FFCC00' : 'var(--bg-tertiary)'}`, backgroundColor: selectedTechniques.has(t) ? 'rgba(255,204,0,0.1)' : 'var(--bg-secondary)', color: selectedTechniques.has(t) ? '#FFCC00' : 'var(--text-secondary)', cursor: 'pointer' }}
              >{t}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Area */}
      <div style={{ flex: 1, overflowY: 'auto', backgroundColor: 'var(--bg-secondary)', padding: '24px' }}>
        
        {processedEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', backgroundColor: 'var(--bg-primary)', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
            No telemetry events found matching the current filters.
          </div>
        ) : (
          <div style={{ backgroundColor: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden' }}>
            
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  <th style={{ padding: '12px 16px', width: '40px' }}></th>
                  <th style={{ padding: '12px 16px', cursor: 'pointer' }} onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12}/> Timestamp {sortDir === 'asc' ? '↑' : '↓'}
                    </div>
                  </th>
                  <th style={{ padding: '12px 16px' }}>Event ID</th>
                  <th style={{ padding: '12px 16px' }}>Type</th>
                  <th style={{ padding: '12px 16px' }}>Host / User</th>
                  <th style={{ padding: '12px 16px' }}>Process</th>
                  <th style={{ padding: '12px 16px' }}>Technique</th>
                </tr>
              </thead>
              <tbody>
                {processedEvents.map((e, index) => {
                  const isExpanded = expandedRows.has(e.event_id);
                  return (
                    <React.Fragment key={`${e.event_id}-${index}`}>
                      <tr 
                        onClick={() => toggleRow(e.event_id)}
                        style={{ 
                          borderTop: '1px solid var(--bg-tertiary)', 
                          cursor: 'pointer',
                          backgroundColor: isExpanded ? 'rgba(255,255,255,0.02)' : 'transparent'
                        }}
                      >
                        <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>
                          {isExpanded ? <ChevronDown size={16}/> : <ChevronRight size={16}/>}
                        </td>
                        <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                          {new Date(e.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                        </td>
                        <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                          {e.event_id}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {e.event_type}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)' }}><Server size={12} color="#AF52DE"/> {e.host_id}</span>
                            {e.user_id && <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}><User size={12} color="#FF9500"/> {e.user_id}</span>}
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {e.process_name ? (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><TerminalSquare size={12} color="#FF2D55"/> {e.process_name}</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>-</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {e.technique_id ? (
                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', backgroundColor: 'rgba(255, 204, 0, 0.15)', color: '#FFCC00', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
                              <Zap size={10} /> {e.technique_id}
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>-</span>
                          )}
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr style={{ backgroundColor: 'var(--bg-secondary)', borderTop: '1px solid var(--bg-tertiary)' }}>
                          <td colSpan={7} style={{ padding: '20px 40px' }}>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                              <div>
                                <h4 style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', margin: '0 0 12px 0' }}>Event Details</h4>
                                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                                  <tbody>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                      <td style={{ padding: '6px 0', color: 'var(--text-muted)', width: '140px' }}>Source</td>
                                      <td style={{ padding: '6px 0', color: 'var(--text-primary)' }}>{e.source}</td>
                                    </tr>
                                    {e.process_id && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '6px 0', color: 'var(--text-muted)' }}>Process ID</td>
                                        <td style={{ padding: '6px 0', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{e.process_id}</td>
                                      </tr>
                                    )}
                                    {e.parent_process_id && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '6px 0', color: 'var(--text-muted)' }}>Parent PID</td>
                                        <td style={{ padding: '6px 0', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{e.parent_process_id}</td>
                                      </tr>
                                    )}
                                    {e.destination_host && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '6px 0', color: 'var(--text-muted)' }}>Dest Host</td>
                                        <td style={{ padding: '6px 0', color: 'var(--text-primary)' }}>{e.destination_host}</td>
                                      </tr>
                                    )}
                                    {e.destination_ip && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '6px 0', color: 'var(--text-muted)' }}>Dest IP</td>
                                        <td style={{ padding: '6px 0', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{e.destination_ip}</td>
                                      </tr>
                                    )}
                                    {e.technique_name && (
                                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '6px 0', color: 'var(--text-muted)' }}>Technique</td>
                                        <td style={{ padding: '6px 0', color: '#FFCC00' }}>{e.technique_id} - {e.technique_name}</td>
                                      </tr>
                                    )}
                                  </tbody>
                                </table>
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                <div>
                                  <h4 style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Parsed Metadata</h4>
                                  <pre style={{ margin: 0, padding: '12px', backgroundColor: 'var(--bg-primary)', borderRadius: '6px', fontSize: '11px', color: 'var(--text-secondary)', border: '1px solid var(--bg-tertiary)', overflowX: 'auto' }}>
                                    {JSON.stringify(e.metadata || {}, null, 2)}
                                  </pre>
                                </div>
                                {e.raw_reference && (
                                  <div>
                                    <h4 style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', margin: '0 0 8px 0' }}>Raw Reference Data</h4>
                                    <pre style={{ margin: 0, padding: '12px', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '6px', fontSize: '11px', color: 'var(--text-secondary)', border: '1px solid rgba(255,255,255,0.05)', overflowX: 'auto' }}>
                                      {JSON.stringify(e.raw_reference, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </div>

                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
