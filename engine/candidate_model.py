"""
candidate_model.py — CyberScope ReconstructionCandidate Data Model

A ReconstructionCandidate represents one plausible explanation for a
detected ReconstructionGap.

IMPORTANT DISCLAIMERS:
- "Candidate generation proposes plausible explanations from observed
  evidence. It does not establish that a candidate actually occurred."
- "Candidate score represents relative evidence support and is not a
  calibrated probability or accuracy measurement."
- candidate_score must NEVER be presented as "X% accuracy."
  Use "Evidence Support Score" or "Candidate Score" in the UI.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ReconstructionCandidate(BaseModel):
    """
    A single plausible reconstruction candidate for a detected gap.

    Scores are assigned by CandidateScorer; they represent relative
    evidence support across the set of candidates for the same gap.
    They are NOT probabilities and NOT accuracy measurements.
    """

    # --- Identity ---
    candidate_id: str = Field(..., description="Unique candidate identifier")
    gap_id: str = Field(..., description="The ReconstructionGap this candidate addresses")

    # --- What it is ---
    event_type: str = Field(..., description="Expected event type for this candidate")
    technique_id: Optional[str] = Field(None, description="MITRE ATT&CK Technique ID")
    technique_name: Optional[str] = Field(None, description="MITRE ATT&CK Technique Name")
    description: str = Field(..., description="Human-readable explanation of the candidate")
    required_preconditions: List[str] = Field(
        default_factory=list,
        description="Conditions that must hold for this candidate to be plausible"
    )

    # --- Evidence traces (populated by CandidateScorer) ---
    supporting_features: List[str] = Field(
        default_factory=list,
        description="Observed features from the telemetry that support this candidate"
    )
    contradictory_features: List[str] = Field(
        default_factory=list,
        description="Observed features that weaken or contradict this candidate"
    )

    # --- Dimensional scores (0.0–1.0, populated by CandidateScorer) ---
    temporal_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Compatibility of the candidate with the temporal window"
    )
    host_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Compatibility with observed host context"
    )
    user_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Compatibility with observed user context"
    )
    process_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Compatibility with observed process relationships"
    )
    technique_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="How well the candidate bridges the technique transition"
    )
    graph_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Compatibility with the observed attack graph topology"
    )

    # --- Combined result (populated by CandidateScorer) ---
    candidate_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description=(
            "Weighted evidence support score (0.0–1.0). "
            "Higher = more observed evidence supports this candidate. "
            "NOT a calibrated probability. NOT an accuracy metric."
        )
    )
    rank: int = Field(
        0, ge=0,
        description="Rank among candidates for the same gap (1 = best supported)"
    )
