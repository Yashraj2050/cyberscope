import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AppLayout } from './layouts/AppLayout';
import { InvestigationLayout } from './layouts/InvestigationLayout';

import { CasesList } from './routes/CasesList';
import { EvaluationView } from './routes/EvaluationView';
import { SettingsView } from './routes/SettingsView';
import { InvestigationOverview } from './routes/InvestigationOverview';
import { TimelineView } from './routes/TimelineView';
import { AttackGraphView } from './routes/AttackGraphView';
import { TelemetryView } from './routes/TelemetryView';
import { AiAssistantView } from './routes/AiAssistantView';
import { GapsView } from './routes/GapsView';
import { CandidatesView } from './routes/CandidatesView';
import { EvidenceView } from './routes/EvidenceView';
import { VerificationView } from './routes/VerificationView';
import { ReportsView } from './routes/ReportsView';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CasesList />} />
          <Route path="/evaluation" element={<EvaluationView />} />
          <Route path="/settings" element={<SettingsView />} />
        </Route>

        <Route element={<InvestigationLayout />}>
          <Route path="/cases/:caseId" element={<InvestigationOverview />} />
          <Route path="/cases/:caseId/timeline" element={<TimelineView />} />
          <Route path="/cases/:caseId/graph" element={<AttackGraphView />} />
          <Route path="/cases/:caseId/telemetry" element={<TelemetryView />} />
          <Route path="/cases/:caseId/gaps" element={<GapsView />} />
          <Route path="/cases/:caseId/candidates" element={<CandidatesView />} />
          <Route path="/cases/:caseId/evidence" element={<EvidenceView />} />
          <Route path="/cases/:caseId/verification" element={<VerificationView />} />
          <Route path="/cases/:caseId/ai" element={<AiAssistantView />} />
          <Route path="/cases/:caseId/report" element={<ReportsView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
