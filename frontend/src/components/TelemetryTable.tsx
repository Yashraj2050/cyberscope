import React from 'react';
import { type CyberEvent, type ReconstructionGap } from '../services/api';

interface TelemetryTableProps {
  events: CyberEvent[];
  gap?: ReconstructionGap | null;
  onSelectEvent: (event: CyberEvent) => void;
}

export function TelemetryTable({ events, gap, onSelectEvent }: TelemetryTableProps) {
  if (!events || events.length === 0) {
    return <div className="empty-state">NO TELEMETRY AVAILABLE</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <div className="section-header">01 TELEMETRY</div>
      <table className="data-table">
        <thead>
          <tr>
            <th>TIME</th>
            <th>EVENT ID</th>
            <th>HOST</th>
            <th>USER</th>
            <th>PROCESS</th>
            <th>EVENT TYPE</th>
            <th>TECHNIQUE</th>
            <th>SOURCE</th>
          </tr>
        </thead>
        <tbody>
          {events.map(ev => {
            // Extract HH:MM:SS from ISO string
            const timeStr = new Date(ev.timestamp).toLocaleTimeString();
            const isGapSource = gap && gap.previous_event_id === ev.event_id;
            return (
              <React.Fragment key={ev.event_id}>
                <tr onClick={() => onSelectEvent(ev)}>
                  <td className="mono">{timeStr}</td>
                  <td className="mono">{ev.event_id}</td>
                  <td className="mono">{ev.host_id}</td>
                  <td className="mono">{ev.user_id || '-'}</td>
                  <td className="mono">{ev.process_name || '-'}</td>
                  <td>{ev.event_type}</td>
                  <td className="mono">{ev.technique_id || '-'}</td>
                  <td className="mono">{ev.source}</td>
                </tr>
                {isGapSource && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', backgroundColor: 'rgba(255,159,10,0.1)', color: 'var(--status-gap)', fontWeight: 'bold', padding: '16px', letterSpacing: '2px' }}>
                      ↓<br/>████ TELEMETRY GAP ████<br/>↓
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
