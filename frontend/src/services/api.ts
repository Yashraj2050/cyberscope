export interface CyberEvent {
  event_id: string;
  timestamp: string;
  host_id: string;
  user_id: string | null;
  process_name: string | null;
  process_id: string | null;
  event_type: string;
  source: string;
  technique_id: string | null;
  technique_name: string | null;
  raw_data: Record<string, any>;
}

export interface DetectionSignals {
  temporal: boolean;
  host_continuity: boolean;
  user_continuity: boolean;
  process_relationship: boolean;
  technique_transition: boolean;
  behavioral_prerequisite: boolean;
}

export interface ReconstructionGap {
  gap_id: string;
  previous_event_id: string;
  next_event_id: string;
  start_timestamp: string;
  end_timestamp: string;
  affected_host: string | null;
  affected_user: string | null;
  temporal_gap_seconds: number;
  previous_event_type: string;
  next_event_type: string;
  detection_signals: DetectionSignals;
  gap_score: number;
  status: string;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  [key: string]: any;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  [key: string]: any;
}

export interface AttackGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ReconstructionCandidate {
  candidate_id: string;
  gap_id: string;
  event_type: string;
  technique_id: string;
  technique_name: string;
  description: string;
  candidate_score: number;
  deterministic_score: number;
  ml_ranking_score: number | null;
  final_ranking_score: number;
  rank_method: string;
  model_version: string | null;
  temporal_score: number;
  host_score: number;
  user_score: number;
  process_score: number;
  technique_score: number;
  graph_score: number;
  rank: number;
  supporting_features: string[];
  contradictory_features: string[];
}

export interface ReconstructionResult {
  reconstruction_id: string;
  gap_id: string;
  status: "OBSERVED" | "INFERRED" | "UNKNOWN";
  candidate_id: string | null;
  event_type: string | null;
  technique_id: string | null;
  technique_name: string | null;
  candidate_score: number | null;
  verification_score: number;
  confidence_label: "HIGH" | "MEDIUM" | "LOW";
  supporting_evidence: string[];
  missing_evidence: string[];
  contradictory_evidence: string[];
  verification_checks: Record<string, "PASS" | "FAIL" | "UNKNOWN">;
  explanation: string;
}

export interface AnalysisMetadata {
  ml_model_version: string | null;
  ml_feature_schema_version: string | null;
  ml_dataset_version: string | null;
  ranker_mode: string;
  hybrid_alpha: number | null;
  ml_model_available: boolean;
  ml_inference_timestamp: string | null;
  ml_status: string | null;
  ml_reason_code: string | null;
}

export interface FullPipelineResult {
  gap: ReconstructionGap;
  candidates: ReconstructionCandidate[];
  result: ReconstructionResult;
  analysis_metadata?: AnalysisMetadata;
}

export interface ScenarioMetadata {
  scenario_id: string;
  scenario_name: string;
  description: string;
  category: string;
  synthetic: boolean;
  event_count: number;
}

const API_BASE = "http://127.0.0.1:8000/api/v1";

export async function getScenarios(): Promise<ScenarioMetadata[]> {
  const response = await fetch(`${API_BASE}/scenarios`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP Error ${response.status}`);
  }
  return response.json();
}

export async function getEvents(scenario: string): Promise<CyberEvent[]> {
  const response = await fetch(`${API_BASE}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP Error ${response.status}`);
  }
  return response.json();
}

export async function getGraph(scenario: string): Promise<AttackGraph> {
  const response = await fetch(`${API_BASE}/graph`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP Error ${response.status}`);
  }
  return response.json();
}

export async function runAnalysis(scenario: string, ranker_mode: string = "DETERMINISTIC", hybrid_alpha: number = 0.70): Promise<FullPipelineResult[]> {
  console.log("CYBERSCOPE REQUEST", {
    url: `${API_BASE}/reconstruction/verify`,
    method: "POST",
    body: JSON.stringify({ scenario, ranker_mode, hybrid_alpha })
  });

  const response = await fetch(`${API_BASE}/reconstruction/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ scenario, ranker_mode, hybrid_alpha }),
  });
  
  console.log("CYBERSCOPE RESPONSE", {
    status: response.status,
    statusText: response.statusText,
    contentType: response.headers.get("content-type")
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP Error ${response.status}`);
  }
  
  const responseData = await response.json();
  console.log("RAW RESPONSE BODY", responseData);
  return responseData;
}
