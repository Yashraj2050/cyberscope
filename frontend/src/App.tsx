import { useState, useEffect } from 'react';
import { 
  type FullPipelineResult, 
  type ScenarioMetadata, 
  type CyberEvent, 
  type AttackGraph,
  getScenarios, 
  runAnalysis,
  getEvents,
  getGraph
} from './services/api';

import { CommandPalette } from './components/CommandPalette';
import { GraphCanvas } from './components/GraphCanvas';
import { InvestigationInspector } from './components/InvestigationInspector';
import { TelemetryTable } from './components/TelemetryTable';
import { WorkflowIndicator } from './components/WorkflowIndicator';
import { ParametersPanel } from './components/ParametersPanel';

import { Play, RotateCcw, Download, Maximize2, Minimize2 } from 'lucide-react';

type EngineState = 'OFFLINE' | 'READY' | 'ANALYZING' | 'SUCCESS';
type PipelineStage = 'TELEMETRY' | 'GRAPH' | 'GAP' | 'CANDIDATES' | 'VERIFICATION' | 'DECISION';

function App() {
  const [engineState, setEngineState] = useState<EngineState>('READY');
  const [presentationMode, setPresentationMode] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  
  const [scenarios, setScenarios] = useState<ScenarioMetadata[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string>("scenario_001.json");
  
  const [currentStage, setCurrentStage] = useState<PipelineStage>('TELEMETRY');
  
  const [events, setEvents] = useState<CyberEvent[]>([]);
  const [graph, setGraph] = useState<AttackGraph | null>(null);
  const [pipelineResult, setPipelineResult] = useState<FullPipelineResult | null>(null);
  
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Initialize
  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch(() => setEngineState('OFFLINE'));
      
    handleReset(activeScenarioId);
  }, []);

  const handleReset = async (scenarioId: string) => {
    setActiveScenarioId(scenarioId);
    setEngineState('READY');
    setCurrentStage('TELEMETRY');
    setPipelineResult(null);
    setSelectedNode(null);
    setGraph(null);
    
    try {
      const evs = await getEvents(scenarioId);
      setEvents(evs);
    } catch (e) {
      setEngineState('OFFLINE');
    }
  };

  const handleRunAnalysis = async () => {
    setEngineState('ANALYZING');
    
    try {
      // Simulate the pipeline visual steps quickly, but actually we just call the endpoints.
      setCurrentStage('TELEMETRY');
      const evs = await getEvents(activeScenarioId);
      setEvents(evs);
      
      setCurrentStage('GRAPH');
      const g = await getGraph(activeScenarioId);
      setGraph(g);
      
      setCurrentStage('GAP');
      // A small visual delay to show the "pipeline" to the jury, since the backend is extremely fast
      await new Promise(r => setTimeout(r, 600)); 
      
      setCurrentStage('CANDIDATES');
      await new Promise(r => setTimeout(r, 600));
      
      setCurrentStage('VERIFICATION');
      await new Promise(r => setTimeout(r, 600));

      const res = await runAnalysis(activeScenarioId);
      if (res && res.length > 0) {
        setPipelineResult(res[0]); // Demo uses the first gap
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
      scenario: activeScenarioId,
      observed_events: events,
      gap: pipelineResult.gap,
      candidates: pipelineResult.candidates,
      result: pipelineResult.result
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cyberscope_report_${activeScenarioId.replace('.json', '')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`app-container ${presentationMode ? 'presentation-mode' : ''}`}>
      
      {/* HEADER */}
      <header className="topbar">
        <div style={{ fontWeight: 700, letterSpacing: '2px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          CYBERSCOPE <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>|</span> Attack Path Reconstruction & Evidence Analysis
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          
          <div style={{ display: 'flex', gap: '12px', marginRight: '16px', fontSize: '11px', fontWeight: 600 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div className="status-dot ready"></div> LOCAL ENGINE
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div className="status-dot ready"></div> OFFLINE
            </span>
          </div>
          
          <select 
            value={activeScenarioId} 
            onChange={(e) => handleReset(e.target.value)}
            style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--bg-tertiary)', padding: '6px 12px', borderRadius: '4px' }}
          >
            {scenarios.map(s => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.synthetic ? '[DEMO] ' : ''}{s.scenario_name}
              </option>
            ))}
          </select>

          <button className="btn" onClick={() => setPresentationMode(!presentationMode)}>
            {presentationMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            {presentationMode ? 'EXIT PRESENTATION' : 'PRESENTATION MODE'}
          </button>
        </div>
      </header>

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-brand">WORKSTATION</div>
        <div className="engine-status">
          <div className={`status-dot ${engineState.toLowerCase()}`}></div>
          ENGINE: {engineState}
        </div>
        <div style={{ padding: '24px', flex: 1 }}>
          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginBottom: '12px' }} onClick={handleRunAnalysis} disabled={engineState === 'ANALYZING'}>
            <Play size={14} /> RUN ANALYSIS
          </button>
          <button className="btn" style={{ width: '100%', justifyContent: 'center', marginBottom: '12px' }} onClick={() => handleReset(activeScenarioId)}>
            <RotateCcw size={14} /> RESET
          </button>
          <button className="btn" style={{ width: '100%', justifyContent: 'center', marginBottom: '24px' }} onClick={handleExport} disabled={!pipelineResult}>
            <Download size={14} /> EXPORT REPORT
          </button>
        </div>
        <ParametersPanel />
      </aside>

      {/* WORKSPACE */}
      <main className="workspace-container" style={{ position: 'relative' }}>
        {presentationMode && (
          <button 
            className="btn" 
            style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 100, backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} 
            onClick={() => setPresentationMode(false)}
          >
            <Minimize2 size={14} /> EXIT PRESENTATION
          </button>
        )}
        {engineState === 'OFFLINE' && (
          <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 50, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-danger, #ef4444)', marginBottom: '16px' }}>ENGINE OFFLINE / ANALYSIS FAILED</div>
            <div style={{ color: 'var(--text-secondary)' }}>The local backend is unreachable or an analysis step failed.</div>
            <button className="btn btn-primary" style={{ marginTop: '24px' }} onClick={() => window.location.reload()}>RELOAD INTERFACE</button>
          </div>
        )}
        <WorkflowIndicator 
          currentStage={currentStage} 
          decision={pipelineResult ? pipelineResult.result.status : null} 
        />
        <div className="workspace-scrollable">
          <GraphCanvas 
            graph={graph}
            gap={pipelineResult?.gap || null}
            selectedNode={selectedNode}
            onSelectNode={setSelectedNode}
          />
          <TelemetryTable 
            events={events} 
            gap={pipelineResult?.gap || null}
            onSelectEvent={(ev) => setSelectedNode(ev.event_id)} 
          />
        </div>
      </main>

      {/* INSPECTOR */}
      <InvestigationInspector pipelineResult={pipelineResult} />

      <CommandPalette 
        open={commandPaletteOpen}
        setOpen={setCommandPaletteOpen}
        scenarios={scenarios}
        onSelectScenario={handleReset}
        onSwitchView={() => {}}
        onRunAnalysis={handleRunAnalysis}
      />
    </div>
  );
}

export default App;
