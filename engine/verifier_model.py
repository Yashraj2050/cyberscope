"""
verifier_model.py — CyberScope ReconstructionResult Data Model

A ReconstructionResult is the final output of the Evidence Verifier.
It carries the OBSERVED / INFERRED / UNKNOWN classification for a gap.

CRITICAL SEMANTICS:
  OBSERVED  — Direct telemetry explicitly contains evidence of this event.
  INFERRED  — Not directly observed, but multiple independent observed
               evidence pieces make it a sufficiently supported reconstruction.
  UNKNOWN   — Available evidence is insufficient, ambiguous, contradictory,
               or cannot distinguish between plausible candidates.

INVARIANTS:
  1. INFERRED does not mean the event definitely occurred.
  2. confidence_label is NOT a calibrated probability.
     HIGH does not mean "80% probability." It means the evidence strength
     score exceeds a documentation threshold. See evidence_verifier.py.
  3. CyberScope does not treat a model score as proof. A reconstruction
     must pass evidence verification before being classified as INFERRED.
  4. When available evidence cannot distinguish between plausible candidates,
     CyberScope abstains and returns UNKNOWN.
"""

import uuid
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ReconstructionStatus(str, Enum):
    """
    The three and only three allowed classification outcomes.
    Do not add additional status values.
    """
    OBSERVED = "OBSERVED"   # Direct telemetry evidence present
    INFERRED  = "INFERRED"  # Strongly supported reconstruction
    UNKNOWN   = "UNKNOWN"   # Insufficient / ambiguous / contradicted


class ConfidenceLabel(str, Enum):
    """
    Qualitative label for evidence strength.

    HIGH   — verification_score >= 0.80
    MEDIUM — verification_score >= 0.60
    LOW    — verification_score < 0.60 or no candidates generated

    IMPORTANT: These labels are NOT calibrated probabilities.
    Do not present HIGH as "80% probability of correct classification."
    Present as "Evidence Strength: HIGH" in the UI.
    """
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"


class CheckResult(str, Enum):
    """Outcome of a single verification check."""
    PASS    = "PASS"
    FAIL    = "FAIL"
    UNKNOWN = "UNKNOWN"


class ReconstructionResult(BaseModel):
    """
    The authoritative final output of the reconstruction pipeline for one gap.

    One ReconstructionResult is produced per ReconstructionGap.
    If multiple candidates were generated, only the best-supported candidate
    (or UNKNOWN if ambiguous) is reflected here.
    """

    # --- Identity ---
    reconstruction_id: str = Field(
        ..., description="Unique reconstruction result identifier"
    )
    gap_id: str = Field(..., description="The gap this result resolves")

    # --- Classification ---
    status: ReconstructionStatus = Field(
        ...,
        description=(
            "OBSERVED: direct telemetry present. "
            "INFERRED: strongly supported reconstruction. "
            "UNKNOWN: insufficient, ambiguous, or contradicted evidence."
        )
    )

    # --- Top candidate (populated for INFERRED; may be present for UNKNOWN) ---
    candidate_id: Optional[str] = Field(
        None, description="ID of the top-ranked candidate (if any)"
    )
    event_type: Optional[str] = Field(
        None, description="Expected event type of the top candidate"
    )
    technique_id: Optional[str] = Field(
        None, description="MITRE technique ID of the top candidate"
    )
    technique_name: Optional[str] = Field(
        None, description="MITRE technique name of the top candidate"
    )
    candidate_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Evidence support score from CandidateScorer (NOT a probability)"
    )

    # --- Verification result ---
    verification_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Weighted verification score across all checks (0.0–1.0). "
            "NOT a calibrated probability. Reflects how many checks passed."
        )
    )
    confidence_label: ConfidenceLabel = Field(
        ...,
        description=(
            "Qualitative evidence strength label. "
            "NOT a probability. See ConfidenceLabel for semantics."
        )
    )

    # --- Evidence traces ---
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Observed features that support the selected candidate"
    )
    missing_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence that would strengthen the reconstruction but is absent"
    )
    contradictory_evidence: List[str] = Field(
        default_factory=list,
        description="Observed features that weaken or contradict the candidate"
    )

    # --- Individual check results ---
    verification_checks: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-check results: each value is 'PASS', 'FAIL', or 'UNKNOWN'. "
            "Checks: temporal, host, user, process, technique, graph, contradiction."
        )
    )

    # --- Human-readable explanation ---
    explanation: str = Field(
        ...,
        description=(
            "Evidence-derived explanation for the classification. "
            "Generated from actual verification results, not a generic template."
        )
    )

    # --- Metadata ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this result was produced"
    )
