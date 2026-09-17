import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  type FullPipelineResult, 
  type CyberEvent, 
  type AttackGraph,
  getEvents,
  getGraph,
  runAnalysis
} from '../services/api';

import { GraphCanvas } from '../components/GraphCanvas';
import { InvestigationInspector } from '../components/InvestigationInspector';
import { ParametersPanel } from '../components/ParametersPanel';
import { AIAssistant } from '../components/AIAssistant';
import { TelemetryTable } from '../components/TelemetryTable';
import { WorkflowIndicator } from '../components/WorkflowIndicator';

type EngineState = 'OFFLINE' | 'READY' | 'ANALYZING' | 'SUCCESS';
type PipelineStage = 'TELEMETRY' | 'GRAPH' | 'GAP' | 'CANDIDATES' | 'VERIFICATION' | 'DECISION';

export function InvestigationOverview() {
  const { caseId } = useParams();
  
  // Local state for the demo implementation
  const [engineState, setEngineState] = useState<EngineState>('READY');
  const [currentStage, setCurrentStage] = useState<PipelineStage>('TELEMETRY');
  const [events, setEvents] = useState<CyberEvent[]>([]);
  const [graph, setGraph] = useState<AttackGraph | null>(null);
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResult | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [rankerMode, setRankerMode] = useState<string>('DETERMINISTIC');
  const [hybridAlpha, setHybridAlpha] = useState<number>(0.70);

  useEffect(() => {
    // Treat the caseId as the scenario file for the demo
    const scenarioId = (caseId && caseId.includes(".json")) ? caseId : "scenario_001.json";
    
    getEvents(scenarioId).then(setEvents).catch(console.error);
    
    // Automatically run the analysis to preserve the demo state
    handleRunAnalysis(scenarioId);
  }, [caseId]);

  const handleRunAnalysis = async (scenarioId: string, mode: string = rankerMode, alpha: number = hybridAlpha) => {
    setEngineState('ANALYZING');
    try {
      setCurrentStage('TELEMETRY');
      const evs = await getEvents(scenarioId);
      setEvents(evs);
      
      setCurrentStage('GRAPH');
      const g = await getGraph(scenarioId);
      setGraph(g);
      
      setCurrentStage('GAP');
      await new Promise(r => setTimeout(r, 300)); 
      
      setCurrentStage('CANDIDATES');
      await new Promise(r => setTimeout(r, 300));
      
      setCurrentStage('VERIFICATION');
      await new Promise(r => setTimeout(r, 300));

      const res = await runAnalysis(scenarioId, mode, alpha);
      if (res && res.length > 0) {
        setPipelineResult(res[0]);
        setCurrentStage('DECISION');
        setEngineState('SUCCESS');
      }
    } catch (err) {
      console.error(err);
      setEngineState('OFFLINE');
    }
  };

  const handleExport = () => {
    if (!pipelineResult) return;
    const report = {
      app: 'CyberScope',
      scenario: caseId,
      observed_events: events,
      gap: pipelineResult.gap,
      candidates: pipelineResult.candidates,
      result: pipelineResult.result
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cyberscope_report_${(caseId || "scenario_001").replace('.json', '')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      
      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--bg-tertiary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Investigation Workflow
          </div>
          <button 
            className="btn btn-primary" 
            onClick={handleExport} 
            disabled={!pipelineResult}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            EXPORT REPORT
          </button>
        </div>
        <WorkflowIndicator 
          currentStage={currentStage} 
          decision={pipelineResult ? pipelineResult.result.status : null} 
        />
      </div>

      {engineState === 'OFFLINE' && (
        <div style={{ color: 'var(--color-danger)', fontWeight: 'bold' }}>Engine Offline</div>
      )}
      
      {pipelineResult?.analysis_metadata?.ml_status === 'UNAVAILABLE' && pipelineResult?.analysis_metadata?.ranker_mode === 'DETERMINISTIC_FALLBACK' && (
        <div style={{ backgroundColor: 'var(--color-warning-transparent)', border: '1px solid var(--color-warning)', color: 'var(--color-warning)', padding: '12px 16px', borderRadius: '4px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          ML unavailable — deterministic fallback active
        </div>
      )}

      <div style={{ display: 'flex', gap: '24px', flex: 1, minHeight: '400px' }}>
        <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div style={{ flex: 1, backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--bg-tertiary)', fontWeight: 600, fontSize: '12px', color: 'var(--text-muted)' }}>
              ATTACK GRAPH
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              <GraphCanvas 
                graph={graph}
                gap={pipelineResult?.gap || null}
                selectedNode={selectedNode}
                onSelectNode={setSelectedNode}
              />
            </div>
          </div>

        </div>

        <div style={{ flex: 1, minWidth: '350px' }}>
          <InvestigationInspector pipelineResult={pipelineResult} />
        </div>
        
        <div style={{ width: '350px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden' }}>
            <ParametersPanel 
              rankerMode={rankerMode} 
              setRankerMode={setRankerMode} 
              hybridAlpha={hybridAlpha} 
              setHybridAlpha={setHybridAlpha} 
            />
          </div>
          
          <div style={{ flex: 1, minHeight: '500px', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden' }}>
            {pipelineResult ? (
              <AIAssistant 
                caseId={caseId || 'scenario_001.json'} 
                decision={pipelineResult.result.status} 
                evidenceStrength={pipelineResult.result.confidence_label} 
              />
            ) : (
              <div style={{ padding: '24px', color: 'var(--text-muted)' }}>
                Run analysis to activate AI Assistant.
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--bg-tertiary)', overflow: 'hidden', height: '300px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--bg-tertiary)', fontWeight: 600, fontSize: '12px', color: 'var(--text-muted)' }}>
          TELEMETRY & EVIDENCE
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <TelemetryTable 
            events={events} 
            gap={pipelineResult?.gap || null}
            onSelectEvent={(ev) => setSelectedNode(ev.event_id)} 
          />
        </div>
      </div>
      
    </div>
  );
}
