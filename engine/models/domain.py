from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

# -------------------------------------------------------------------------
# CORE EVENTS
# -------------------------------------------------------------------------

class CyberEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    timestamp: datetime = Field(..., description="When the event occurred")
    host_id: str = Field(..., description="The host where the event occurred")
    user_id: Optional[str] = None
    process_id: Optional[str] = None
    parent_process_id: Optional[str] = None
    event_type: str = Field(..., description="Category of the event (e.g., ProcessCreate, NetworkConnect)")
    process_name: Optional[str] = None
    source: str = Field(..., description="Sensor or log source (e.g., Sysmon, Windows Event Log)")
    source_event_id: Optional[str] = Field(None, description="Original event ID from the source system")
    technique_id: Optional[str] = Field(None, description="MITRE ATT&CK Technique ID")
    technique_name: Optional[str] = Field(None, description="MITRE ATT&CK Technique Name")
    destination_host: Optional[str] = None
    destination_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional structured context")
    raw_reference: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Original raw event payload")


# -------------------------------------------------------------------------
# RECONSTRUCTION GAP
# -------------------------------------------------------------------------

class GapStatus(str, Enum):
    OPEN = "OPEN"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"

class DetectionSignals(BaseModel):
    temporal: bool = False
    host_continuity: bool = False
    user_continuity: bool = False
    process_relationship: bool = False
    technique_transition: bool = False
    behavioral_prerequisite: bool = False

class ReconstructionGap(BaseModel):
    gap_id: str
    previous_event_id: str
    next_event_id: str
    start_timestamp: datetime
    end_timestamp: datetime
    affected_host: Optional[str] = None
    affected_user: Optional[str] = None
    temporal_gap_seconds: float
    previous_event_type: str
    next_event_type: str
    graph_context: Dict[str, Any] = Field(default_factory=dict)
    detection_signals: DetectionSignals
    gap_score: float = Field(..., ge=0.0, le=1.0)
    status: GapStatus = GapStatus.OPEN


# -------------------------------------------------------------------------
# CANDIDATE
# -------------------------------------------------------------------------

class ReconstructionCandidate(BaseModel):
    candidate_id: str
    gap_id: str
    event_type: str
    technique_id: Optional[str] = None
    technique_name: Optional[str] = None
    description: str
    required_preconditions: List[str] = Field(default_factory=list)
    supporting_features: List[str] = Field(default_factory=list)
    contradictory_features: List[str] = Field(default_factory=list)
    temporal_score: float = Field(0.0, ge=0.0, le=1.0)
    host_score: float = Field(0.0, ge=0.0, le=1.0)
    user_score: float = Field(0.0, ge=0.0, le=1.0)
    process_score: float = Field(0.0, ge=0.0, le=1.0)
    technique_score: float = Field(0.0, ge=0.0, le=1.0)
    graph_score: float = Field(0.0, ge=0.0, le=1.0)
    candidate_score: float = Field(0.0, ge=0.0, le=1.0)
    deterministic_score: float = Field(0.0, ge=0.0, le=1.0)
    ml_ranking_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    final_ranking_score: float = Field(0.0, ge=0.0, le=1.0)
    rank_method: str = "DETERMINISTIC"
    model_version: Optional[str] = None
    rank: int = Field(0, ge=0)


# -------------------------------------------------------------------------
# EVIDENCE & VERIFICATION
# -------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    is_supporting: bool
    provenance_event_ids: List[str] = Field(default_factory=list)

class ReconstructionStatus(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED  = "INFERRED"
    UNKNOWN   = "UNKNOWN"

class ConfidenceLabel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

class CheckResult(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    UNKNOWN = "UNKNOWN"

class ReconstructionResult(BaseModel):
    reconstruction_id: str
    gap_id: str
    status: ReconstructionStatus
    candidate_id: Optional[str] = None
    event_type: Optional[str] = None
    technique_id: Optional[str] = None
    technique_name: Optional[str] = None
    candidate_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    verification_score: float = Field(..., ge=0.0, le=1.0)
    confidence_label: ConfidenceLabel
    supporting_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    verification_checks: Dict[str, str] = Field(default_factory=dict)
    explanation: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -------------------------------------------------------------------------
# INVESTIGATION & CASE MANAGEMENT
# -------------------------------------------------------------------------

class AnalysisMetadata(BaseModel):
    engine_version: str = "1.0.0"
    knowledge_base_version: str = "1.0.0"
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_hash: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    gap_threshold: float = 0.40
    ml_model_version: Optional[str] = None
    ml_feature_schema_version: Optional[str] = None
    ml_dataset_version: Optional[str] = None
    ranker_mode: str = "DETERMINISTIC"
    hybrid_alpha: Optional[float] = None
    ml_model_available: bool = False
    ml_inference_timestamp: Optional[datetime] = None
    ml_status: Optional[str] = None
    ml_reason_code: Optional[str] = None

class InvestigationResult(BaseModel):
    case_id: str
    events: List[CyberEvent]
    graph: Dict[str, Any]
    gaps: List[ReconstructionGap]
    candidates: Dict[str, List[ReconstructionCandidate]]
    verification: Dict[str, ReconstructionResult]
    analysis_metadata: AnalysisMetadata

class InvestigationCase(BaseModel):
    case_id: str = Field(..., description="Unique case identifier")
    title: str
    description: str = ""
    status: str = "OPEN"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyst: str = "Local User"
    tags: List[str] = Field(default_factory=list)
    telemetry_source_metadata: Dict[str, Any] = Field(default_factory=dict)
    engine_version: str = "1.0.0"
    knowledge_base_version: str = "1.0.0"
    has_analysis: bool = False
