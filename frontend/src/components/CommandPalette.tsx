import { useEffect } from 'react';
import { Command } from 'cmdk';
import { type ScenarioMetadata } from '../services/api';
import { Search, Layers, Play } from 'lucide-react';

interface CommandPaletteProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  scenarios: ScenarioMetadata[];
  onSelectScenario: (id: string) => void;
  onRunAnalysis: () => void;
  onSwitchView: (view: string) => void;
}

export function CommandPalette({ open, setOpen, scenarios, onSelectScenario, onRunAnalysis, onSwitchView }: CommandPaletteProps) {
  // Toggle the menu when ⌘K is pressed
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(true);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [setOpen]);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen} label="Global Command Menu">
      <Command.Input placeholder="Search scenarios, hosts, events..." />
      <Command.List>
        <Command.Empty>No results found.</Command.Empty>

        <Command.Group heading="Scenarios">
          {scenarios.map(s => (
            <Command.Item 
              key={s.scenario_id} 
              onSelect={() => {
                onSelectScenario(s.scenario_id);
                onSwitchView('Attack Graph');
                setOpen(false);
              }}
            >
              <Layers size={14} />
              <span>{s.scenario_name}</span>
              <span style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--text-muted)' }}>
                {s.event_count} Events
              </span>
            </Command.Item>
          ))}
        </Command.Group>

        <Command.Group heading="Actions">
          <Command.Item onSelect={() => {
            onRunAnalysis();
            onSwitchView('Attack Graph');
            setOpen(false);
          }}>
            <Play size={14} />
            <span>Run Analysis on Current Scenario</span>
          </Command.Item>
          <Command.Item onSelect={() => {
            onSwitchView('Investigations');
            setOpen(false);
          }}>
            <Search size={14} />
            <span>Search all Evidence...</span>
          </Command.Item>
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  );
}
