import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { type AttackGraph, type ReconstructionGap, getGraph, getGaps } from '../services/api';
import { ZoomIn, ZoomOut, Maximize, Search } from 'lucide-react';

interface NodePos {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export function AttackGraphView() {
  const { caseId } = useParams();
  const scenarioId = (caseId && caseId.includes('.json')) ? caseId : 'scenario_001.json';

  const [graph, setGraph] = useState<AttackGraph | null>(null);
  const [gaps, setGaps] = useState<ReconstructionGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [positions, setPositions] = useState<Record<string, NodePos>>({});
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  // Fetch data
  useEffect(() => {
    setLoading(true);
    Promise.all([
      getGraph(scenarioId),
      getGaps(scenarioId)
    ])
    .then(([g, gps]) => {
      setGraph(g);
      setGaps(gps);
      
      // Initialize layout
      const initialPositions: Record<string, NodePos> = {};
      g.nodes.forEach((n, i) => {
        initialPositions[n.id] = {
          x: Math.cos(i) * 200,
          y: Math.sin(i) * 200,
          vx: 0,
          vy: 0
        };
      });
      setPositions(initialPositions);
      
    })
    .catch(err => setError(err.message || 'Failed to fetch graph data'))
    .finally(() => setLoading(false));
  }, [scenarioId]);

  // Run a simple force-directed layout simulation when graph loads
  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return;

    let currentPos = { ...positions };
    const ITERATIONS = 300;
    const k = 200; // ideal distance
    const kSq = k * k;

    for (let iter = 0; iter < ITERATIONS; iter++) {
      const forces: Record<string, { fx: number, fy: number }> = {};
      graph.nodes.forEach(n => forces[n.id] = { fx: 0, fy: 0 });

      // Repulsion between all nodes
      for (let i = 0; i < graph.nodes.length; i++) {
        for (let j = i + 1; j < graph.nodes.length; j++) {
          const n1 = graph.nodes[i].id;
          const n2 = graph.nodes[j].id;
          const dx = currentPos[n1].x - currentPos[n2].x;
          const dy = currentPos[n1].y - currentPos[n2].y;
          const distSq = dx * dx + dy * dy || 0.1;
          const dist = Math.sqrt(distSq);
          const f = kSq / dist;
          
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          forces[n1].fx += fx;
          forces[n1].fy += fy;
          forces[n2].fx -= fx;
          forces[n2].fy -= fy;
        }
      }

      // Attraction along edges
      graph.edges.forEach(edge => {
        const n1 = edge.source;
        const n2 = edge.target;
        if (!currentPos[n1] || !currentPos[n2]) return;
        
        const dx = currentPos[n1].x - currentPos[n2].x;
        const dy = currentPos[n1].y - currentPos[n2].y;
        const dist = Math.sqrt(dx * dx + dy * dy || 0.1);
        const f = (dist * dist) / k;

        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        forces[n1].fx -= fx;
        forces[n1].fy -= fy;
        forces[n2].fx += fx;
        forces[n2].fy += fy;
      });

      // Gravity towards center
      graph.nodes.forEach(n => {
        const id = n.id;
        const d = Math.sqrt(currentPos[id].x ** 2 + currentPos[id].y ** 2 || 0.1);
        forces[id].fx -= (currentPos[id].x / d) * (d * 0.1);
        forces[id].fy -= (currentPos[id].y / d) * (d * 0.1);
      });

      // Update positions
      const newPos = { ...currentPos };
      graph.nodes.forEach(n => {
        const id = n.id;
        // temperature cooling
        const temp = Math.max(1, 20 * (1 - iter / ITERATIONS));
        let dx = forces[id].fx;
        let dy = forces[id].fy;
        const dist = Math.sqrt(dx * dx + dy * dy || 0.1);
        
        if (dist > temp) {
          dx = (dx / dist) * temp;
          dy = (dy / dist) * temp;
        }
        
        newPos[id] = {
          x: currentPos[id].x + dx,
          y: currentPos[id].y + dy,
          vx: 0, vy: 0
        };
      });
      currentPos = newPos;
    }
    
    setPositions(currentPos);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph]);

  if (loading) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading graph...</div>;
  }
  if (error || !graph) {
    return <div style={{ padding: '40px', color: 'var(--status-fail)' }}>Error: {error}</div>;
  }

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'EVENT': return 'var(--accent-cyan)';
      case 'HOST': return '#AF52DE';
      case 'USER': return '#FF9500';
      case 'PROCESS': return '#FF2D55';
      case 'TECHNIQUE': return '#FFCC00';
      default: return 'var(--text-muted)';
    }
  };

  const selectedNodeData = graph.nodes.find(n => n.id === selectedNodeId);

  // Search filtering
  const highlightedNodes = new Set<string>();
  if (search.trim()) {
    const q = search.toLowerCase();
    graph.nodes.forEach(n => {
      if (
        n.id.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q) ||
        n.label.toLowerCase().includes(q)
      ) {
        highlightedNodes.add(n.id);
      }
    });
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 48px)', boxSizing: 'border-box' }}>
      
      {/* Header & Controls */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--bg-tertiary)', backgroundColor: 'var(--bg-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0' }}>Attack Graph</h2>
          <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <span>Nodes: <strong style={{ color: 'var(--text-primary)' }}>{graph.nodes.length}</strong></span>
            <span>Edges: <strong style={{ color: 'var(--text-primary)' }}>{graph.edges.length}</strong></span>
            <span>Gaps: <strong style={{ color: 'var(--status-gap)' }}>{gaps.length}</strong></span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search graph..."
              style={{
                width: '100%',
                padding: '8px 8px 8px 32px',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--bg-tertiary)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '12px',
                boxSizing: 'border-box'
              }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* Graph Canvas area */}
        <div style={{ flex: 1, backgroundColor: 'var(--bg-secondary)', position: 'relative' }}>
          
          <TransformWrapper
            initialScale={1}
            initialPositionX={400}
            initialPositionY={300}
            minScale={0.1}
            maxScale={4}
            centerOnInit={true}
          >
            {({ zoomIn, zoomOut, resetTransform }) => (
              <>
                <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10, display: 'flex', gap: '8px', backgroundColor: 'var(--bg-primary)', padding: '4px', borderRadius: '6px', border: '1px solid var(--bg-tertiary)' }}>
                  <button onClick={() => zoomIn()} style={{ padding: '6px', backgroundColor: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex' }}><ZoomIn size={16}/></button>
                  <button onClick={() => zoomOut()} style={{ padding: '6px', backgroundColor: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex' }}><ZoomOut size={16}/></button>
                  <button onClick={() => resetTransform()} style={{ padding: '6px', backgroundColor: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex' }}><Maximize size={16}/></button>
                </div>

                <TransformComponent wrapperStyle={{ width: '100%', height: '100%' }}>
                  <svg width="2000" height="2000" style={{ overflow: 'visible' }}>
                    <g transform="translate(1000, 1000)">
                    {/* Edges */}
                    {graph.edges.map((e, i) => {
                      const p1 = positions[e.source];
                      const p2 = positions[e.target];
                      if (!p1 || !p2) return null;
                      return (
                        <g key={`edge-${i}`}>
                          <line 
                            x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} 
                            stroke="rgba(255,255,255,0.2)" 
                            strokeWidth={2}
                          />
                          <text 
                            x={(p1.x + p2.x)/2} y={(p1.y + p2.y)/2} 
                            fill="rgba(255,255,255,0.4)" 
                            fontSize="8"
                            textAnchor="middle"
                            dy="-4"
                          >
                            {e.relationship}
                          </text>
                        </g>
                      );
                    })}

                    {/* Gap Annotations */}
                    {gaps.map((g) => {
                      const p1 = positions[g.previous_event_id];
                      const p2 = positions[g.next_event_id];
                      if (!p1 || !p2) return null;
                      
                      const mx = (p1.x + p2.x) / 2;
                      const my = (p1.y + p2.y) / 2;
                      
                      return (
                        <g key={`gap-${g.gap_id}`}>
                          <line 
                            x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} 
                            stroke="var(--status-gap)" 
                            strokeWidth={3}
                            strokeDasharray="5,5"
                          />
                          <rect 
                            x={mx - 60} y={my - 20} 
                            width="120" height="40" 
                            rx="4"
                            fill="var(--bg-primary)"
                            stroke="var(--status-gap)"
                            strokeWidth="2"
                            strokeDasharray="4,4"
                          />
                          <text x={mx} y={my - 2} fill="var(--status-gap)" fontSize="10" fontWeight="bold" textAnchor="middle">DETECTED GAP</text>
                          <text x={mx} y={my + 10} fill="var(--text-muted)" fontSize="8" textAnchor="middle">Evidence incomplete</text>
                        </g>
                      );
                    })}

                    {/* Nodes */}
                    {graph.nodes.map(n => {
                      const p = positions[n.id];
                      if (!p) return null;
                      const isSelected = selectedNodeId === n.id;
                      const isDimmed = search.trim().length > 0 && !highlightedNodes.has(n.id);

                      return (
                        <g 
                          key={n.id} 
                          transform={`translate(${p.x},${p.y})`} 
                          onClick={() => setSelectedNodeId(n.id)}
                          style={{ cursor: 'pointer', opacity: isDimmed ? 0.2 : 1 }}
                        >
                          <circle 
                            r={14} 
                            fill={getNodeColor(n.type)} 
                            stroke={isSelected ? 'white' : 'var(--bg-primary)'}
                            strokeWidth={isSelected ? 3 : 2}
                          />
                          <text 
                            y={24} 
                            fill={isSelected ? 'white' : 'var(--text-secondary)'} 
                            fontSize="11" 
                            textAnchor="middle" 
                            fontWeight={isSelected ? 700 : 400}
                          >
                            {n.id}
                          </text>
                        </g>
                      );
                    })}
                    </g>
                  </svg>
                </TransformComponent>
              </>
            )}
          </TransformWrapper>
          
          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '16px', left: '16px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '8px', backgroundColor: 'var(--bg-primary)', padding: '12px', borderRadius: '6px', border: '1px solid var(--bg-tertiary)', fontSize: '11px' }}>
            <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>Legend</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getNodeColor('EVENT') }}></div> Observed Event</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getNodeColor('HOST') }}></div> Host</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getNodeColor('PROCESS') }}></div> Process</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getNodeColor('USER') }}></div> User</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: getNodeColor('TECHNIQUE') }}></div> Technique</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '10px', height: '2px', borderTop: '2px dashed var(--status-gap)' }}></div> Detected Gap</div>
          </div>
        </div>

        {/* Inspector Panel */}
        {selectedNodeData && (
          <div style={{ width: '320px', backgroundColor: 'var(--bg-primary)', borderLeft: '1px solid var(--bg-tertiary)', overflowY: 'auto' }}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--bg-tertiary)' }}>
              <div style={{ fontSize: '11px', color: getNodeColor(selectedNodeData.type), fontWeight: 700, marginBottom: '8px' }}>{selectedNodeData.type}</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)' }}>{selectedNodeData.id}</div>
            </div>
            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Label</div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{selectedNodeData.label || 'N/A'}</div>
              </div>
              
              {/* Render dynamic attributes */}
              {Object.entries(selectedNodeData).map(([k, v]) => {
                if (['id', 'type', 'label'].includes(k)) return null;
                return (
                  <div key={k}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>{k}</div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      {typeof v === 'object' ? <pre style={{ margin: 0, fontSize: '11px' }}>{JSON.stringify(v, null, 2)}</pre> : String(v)}
                    </div>
                  </div>
                )
              })}

              <div style={{ marginTop: '24px', padding: '12px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                Select nodes on the graph to inspect actual telemetry attributes. No hidden ground truth is exposed in this view.
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
