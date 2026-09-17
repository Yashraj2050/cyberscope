import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AppLayout } from './layouts/AppLayout';
import { InvestigationLayout } from './layouts/InvestigationLayout';

import { CasesList } from './routes/CasesList';
import { InvestigationOverview } from './routes/InvestigationOverview';
import { AiAssistantView } from './routes/AiAssistantView';

function PlaceholderView({ title }: { title: string }) {
  return (
    <div style={{ padding: '40px', color: 'var(--text-secondary)' }}>
      <h2>{title}</h2>
      <p>This view is under construction in Phase 1.</p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CasesList />} />
          <Route path="/evaluation" element={<PlaceholderView title="Evaluation" />} />
          <Route path="/settings" element={<PlaceholderView title="Settings" />} />
        </Route>

        <Route element={<InvestigationLayout />}>
          <Route path="/cases/:caseId" element={<InvestigationOverview />} />
          <Route path="/cases/:caseId/timeline" element={<PlaceholderView title="Timeline" />} />
          <Route path="/cases/:caseId/graph" element={<PlaceholderView title="Attack Graph" />} />
          <Route path="/cases/:caseId/telemetry" element={<PlaceholderView title="Telemetry" />} />
          <Route path="/cases/:caseId/gaps" element={<PlaceholderView title="Gaps" />} />
          <Route path="/cases/:caseId/candidates" element={<PlaceholderView title="Candidates" />} />
          <Route path="/cases/:caseId/evidence" element={<PlaceholderView title="Evidence" />} />
          <Route path="/cases/:caseId/verification" element={<PlaceholderView title="Verification" />} />
          <Route path="/cases/:caseId/ai" element={<AiAssistantView />} />
          <Route path="/cases/:caseId/report" element={<PlaceholderView title="Reports" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
