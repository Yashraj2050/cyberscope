import { type AttackGraph, type ReconstructionGap } from '../services/api';
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { ZoomIn, ZoomOut, Maximize, RotateCcw } from 'lucide-react';

interface GraphCanvasProps {
  graph: AttackGraph | null;
  gap: ReconstructionGap | null;
  selectedNode: string | null;
  onSelectNode: (nodeId: string) => void;
}

export function GraphCanvas({ graph, gap, selectedNode, onSelectNode }: GraphCanvasProps) {
  if (!graph) return <div className="graph-container" style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>No graph data available.</div>;

  return (
    <div className="graph-container">
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={3}
        centerOnInit={true}
        limitToBounds={false}
      >
        {({ zoomIn, zoomOut, resetTransform, centerView }) => (
          <>
            <div className="graph-controls">
              <button className="graph-ctrl-btn" onClick={() => centerView()} title="Fit Graph"><Maximize size={16} /></button>
              <button className="graph-ctrl-btn" onClick={() => zoomIn()} title="Zoom In"><ZoomIn size={16} /></button>
              <button className="graph-ctrl-btn" onClick={() => zoomOut()} title="Zoom Out"><ZoomOut size={16} /></button>
              <button className="graph-ctrl-btn" onClick={() => resetTransform()} title="Reset View"><RotateCcw size={16} /></button>
            </div>

            <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }} contentStyle={{ width: "100%", height: "100%", display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ display: 'flex', gap: '48px', padding: '100px', alignItems: 'center' }}>
                
                {graph.nodes.map((node, index) => {
                  const isSelected = selectedNode === node.id;
                  const isPrev = gap?.previous_event_id === node.id;
                  
                  return (
                    <div key={node.id} style={{ display: 'flex', alignItems: 'center', gap: '48px' }}>
                      <div 
                        className={`graph-node ${isSelected ? 'selected' : ''}`}
                        style={{
                          border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--bg-tertiary)',
                          cursor: 'pointer'
                        }}
                        onClick={() => onSelectNode(node.id)}
                      >
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
                          {node.type}
                        </div>
                        <div style={{ fontWeight: 600, marginBottom: '8px' }}>{node.id}</div>
                        {node.host && <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>HOST: {node.host}</div>}
                        {node.user && <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>USER: {node.user}</div>}
                        {node.technique_id && <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>TECHNIQUE: {node.technique_id}</div>}
                      </div>

                      {/* Render Gap if this is the previous event */}
                      {isPrev && gap && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '48px' }}>
                          <div style={{ color: 'var(--text-muted)' }}>→</div>
                          <div className="graph-node gap" style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '10px', color: 'var(--status-gap)', marginBottom: '8px', fontWeight: 700 }}>MISSING TELEMETRY</div>
                            <div className="mono">{gap.gap_id}</div>
                            <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                              GAP SCORE: {gap.gap_score.toFixed(2)}
                            </div>
                          </div>
                          <div style={{ color: 'var(--text-muted)' }}>→</div>
                        </div>
                      )}
                      
                      {/* Normal Edge */}
                      {index < graph.nodes.length - 1 && !isPrev && (
                         <div style={{ color: 'var(--text-muted)' }}>→</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}
