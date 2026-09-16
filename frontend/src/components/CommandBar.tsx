import { Play, RotateCcw } from 'lucide-react';
import { type ScenarioMetadata } from '../services/api';

interface CommandBarProps {
  isLoading: boolean;
  scenarios: ScenarioMetadata[];
  selectedScenarioId: string;
  onSelectScenario: (id: string) => void;
  onRunAnalysis: () => void;
  onResetDemo: () => void;
}

export function CommandBar({ 
  isLoading, 
  scenarios, 
  selectedScenarioId, 
  onSelectScenario, 
  onRunAnalysis, 
  onResetDemo 
}: CommandBarProps) {
  return (
    <header className="command-bar">
      <div className="brand">
        <h1>CYBERSCOPE</h1>
        <span className="subtitle">Offline Attack Path Reconstruction</span>
        <span className="badge badge-unknown" style={{ marginLeft: '16px' }}>DEMO MODE</span>
      </div>

      <div className="header-right">
        <div className="offline-indicator">
          <div className="dot"></div>
          LOCAL ENGINE OFFLINE
        </div>

        <div className="scenario-selector">
          <select 
            disabled={isLoading} 
            value={selectedScenarioId}
            onChange={(e) => onSelectScenario(e.target.value)}
          >
            {scenarios.map(s => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.scenario_name}
              </option>
            ))}
          </select>
          
          <button 
            className="run-btn" 
            onClick={onRunAnalysis}
            disabled={isLoading || !selectedScenarioId}
          >
            <Play size={12} />
            {isLoading ? 'ANALYZING...' : 'RUN ANALYSIS'}
          </button>

          <button 
            className="run-btn" 
            onClick={onResetDemo}
            disabled={isLoading}
            title="Reset Demo"
          >
            <RotateCcw size={12} />
            RESET
          </button>
        </div>
      </div>
    </header>
  );
}
